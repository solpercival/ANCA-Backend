.PHONY: install lint test bench up up-full down build migrate migrate-down migrate-status db-reset revision ingest seed-alarms models eval fmt smoke bootstrap restart retest
VENV=.venv/bin
# Reserves the GPU for Ollama when an NVIDIA GPU is present; plain CPU compose otherwise.
COMPOSE := docker compose $(shell command -v nvidia-smi >/dev/null 2>&1 && echo -f docker-compose.yml -f docker-compose.gpu.yml)

bootstrap:      ## first run on a fresh machine: docker + venv + models + ingest + smoke
	bash scripts/bootstrap.sh

install:
	python3.12 -m venv .venv && $(VENV)/pip install -e ".[dev]"

fmt:
	$(VENV)/ruff format . && $(VENV)/ruff check --fix .

lint:
	$(VENV)/ruff check . && $(VENV)/pylint src/rag_engine || true

bench:          ## warm multi-query latency + correctness benchmark against the running stack
	bash scripts/bench.sh

test:
	$(VENV)/pytest -q

up:            ## application + postgres + redis + Ollama
	$(COMPOSE) up --build

up-full:       ## + langfuse
	$(COMPOSE) --profile observability up --build

models:        ## start Ollama and download the local models
	$(COMPOSE) up -d ollama
	$(COMPOSE) exec ollama ollama pull qwen3-embedding:0.6b
	$(COMPOSE) exec ollama ollama pull qwen3:4b-instruct-2507-q4_K_M

down:
	$(COMPOSE) down

build:          ## rebuild the orchestrator + migrate + ingestion images
	$(COMPOSE) build orchestrator migrate ingestion

migrate:        ## apply schema migrations (alembic upgrade head) in the migrate container
	$(COMPOSE) run --rm --build migrate

migrate-down:   ## roll back ONE migration (alembic downgrade -1)
	$(COMPOSE) run --rm --build migrate alembic downgrade -1

# The orchestrator's pooled connections cache the vector type's OID, which the reset
# recreates (downgrade drops the extension), so stop it; it reconnects fresh on restart.
db-reset:       ## DESTRUCTIVE: drop the whole schema and rebuild it empty (then: make ingest && make restart)
	$(COMPOSE) stop orchestrator
	$(COMPOSE) run --rm --build migrate sh -c "alembic downgrade base && alembic upgrade head"
	@echo "Schema rebuilt empty. Next: make ingest && make restart"

revision:       ## new empty migration: make revision m="add response.rating"
	@test -n "$(m)" || { echo 'usage: make revision m="short description"'; exit 1; }
	$(VENV)/alembic revision -m "$(m)"

migrate-status: ## show the current revision and the history
	$(COMPOSE) run --rm --build migrate sh -c "alembic current && alembic history"

ingest:        ## offline: chunk docs -> embed -> pgvector
	$(MAKE) migrate
	$(MAKE) models
	$(COMPOSE) run --rm --build ingestion

seed-alarms:    ## load alarms.sample.json into the alarm catalogue (no embedding)
	$(COMPOSE) run --rm --build ingestion python -m ingestion.seed_alarms

smoke:          ## end-to-end smoke test: auth -> resolve -> chat against the running stack
	bash scripts/smoke_e2e.sh

eval:          ## run Ragas/DeepEval against docs/docs-proto/starter-kit/alarms/reference-answers.json
	bash scripts/run_eval.sh

restart:        ## rebuild + recreate the orchestrator (GPU override included) and wait until healthy
	$(COMPOSE) up -d --build orchestrator

retest:         ## after a code change: unit tests -> restart orchestrator -> bench -> eval
	@echo "=== UNIT TESTS ==="
	POSTGRES_HOST=localhost $(VENV)/pytest -q --tb=line
	@echo "=== RESTART ORCHESTRATOR ==="
	$(MAKE) restart
	@echo "=== BENCH ==="
	bash scripts/bench.sh
	@echo "=== EVAL ==="
	bash scripts/run_eval.sh
