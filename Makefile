# Developer entry points. `make` (or `make help`) lists the targets.
#
# Every docker target goes through $(COMPOSE), which adds docker-compose.gpu.yml when
# an NVIDIA GPU is present. Don't use a plain `docker compose up` for app services:
# it recreates ollama/orchestrator without their GPU reservation, and generation and
# the reranker silently fall back to CPU.
#
# Database schema: Alembic migrations in migrations/ are the only schema definition.
# The one-shot `migrate` compose service applies them, and up/restart/ingest depend
# on it, so pending migrations always run before the app or ingestion touch the DB.

.PHONY: help bootstrap install fmt lint test \
        up up-full down build restart models \
        migrate migrate-status migrate-down revision db-reset \
        ingest seed-alarms \
        smoke bench eval retest

.DEFAULT_GOAL := help

VENV = .venv/bin
COMPOSE := docker compose $(shell command -v nvidia-smi >/dev/null 2>&1 && echo -f docker-compose.yml -f docker-compose.gpu.yml)

help:           ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

# --- setup ---------------------------------------------------------------------

bootstrap:      ## first run on a fresh machine: docker + venv + models + ingest + smoke
	bash scripts/bootstrap.sh

install:        ## create .venv and install the project with dev deps (no model deps)
	python3.12 -m venv .venv && $(VENV)/pip install -e ".[dev]"

# --- code quality ----------------------------------------------------------------

fmt:            ## format and auto-fix with ruff
	$(VENV)/ruff format . && $(VENV)/ruff check --fix .

lint:           ## ruff + pylint (report only; never fails the build)
	$(VENV)/ruff check . && $(VENV)/pylint src/rag_engine || true

test:           ## unit tests (integration tests needing live services are deselected)
	$(VENV)/pytest -q

# --- stack -----------------------------------------------------------------------

up:             ## run the stack in the foreground: migrate + orchestrator + postgres + redis + Ollama
	$(COMPOSE) up --build

up-full:        ## as `up`, plus Langfuse (observability profile)
	$(COMPOSE) --profile observability up --build

down:           ## stop and remove the stack's containers (volumes/data are kept)
	$(COMPOSE) down

build:          ## rebuild the orchestrator, migrate and ingestion images
	$(COMPOSE) build orchestrator migrate ingestion

restart:        ## rebuild and recreate the orchestrator in the background (runs migrate first)
	$(COMPOSE) up -d --build orchestrator

models:         ## start Ollama and pull the embedding + generation models
	$(COMPOSE) up -d ollama
	$(COMPOSE) exec ollama ollama pull qwen3-embedding:0.6b
	$(COMPOSE) exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M

# --- database migrations (Alembic) -----------------------------------------------

migrate:        ## apply pending migrations (alembic upgrade head)
	$(COMPOSE) run --rm --build migrate

migrate-status: ## show the database's current revision and the revision history
	$(COMPOSE) run --rm --build migrate sh -c "alembic current && alembic history"

migrate-down:   ## roll back one migration (alembic downgrade -1)
	$(COMPOSE) run --rm --build migrate alembic downgrade -1

# Runs on the host venv: generating the file needs no database.
revision:       ## create an empty migration: make revision m="add response.rating"
	@test -n "$(m)" || { echo 'usage: make revision m="short description"'; exit 1; }
	$(VENV)/alembic revision -m "$(m)"

# Downgrading to base drops the vector extension and the upgrade recreates it with a
# new type OID. The orchestrator's pooled connections cached the old OID, so it is
# stopped here and reconnects cleanly on the next start.
db-reset:       ## DESTRUCTIVE: drop all tables and data, rebuild an empty schema
	$(COMPOSE) stop orchestrator
	$(COMPOSE) run --rm --build migrate sh -c "alembic downgrade base && alembic upgrade head"
	@echo "Schema rebuilt empty. Next: make ingest && make restart"

# --- data ------------------------------------------------------------------------

ingest:         ## migrate, pull models, then chunk + embed the docs into pgvector
	$(MAKE) migrate
	$(MAKE) models
	$(COMPOSE) run --rm --build ingestion

seed-alarms:    ## load alarms.sample.json into the alarm catalogue only (no embedding)
	$(COMPOSE) run --rm --build ingestion python -m ingestion.seed_alarms

# --- checks against the running stack ----------------------------------------------

smoke:          ## end-to-end smoke test: auth -> resolve -> chat
	bash scripts/smoke_e2e.sh

bench:          ## warm latency + answer check over sample alarm codes, with per-stage timings
	bash scripts/bench.sh

eval:           ## score retrieval and answers against the gold reference answers
	bash scripts/run_eval.sh

# POSTGRES_HOST=localhost lets the host-side tests reach the stack's published port.
retest:         ## after a code change: unit tests -> restart orchestrator -> bench -> eval
	@echo "=== UNIT TESTS ==="
	POSTGRES_HOST=localhost $(VENV)/pytest -q --tb=line
	@echo "=== RESTART ORCHESTRATOR ==="
	$(MAKE) restart
	@echo "=== BENCH ==="
	bash scripts/bench.sh
	@echo "=== EVAL ==="
	bash scripts/run_eval.sh
