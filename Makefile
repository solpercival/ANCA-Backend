.PHONY: install lint test up down build ingest models eval fmt smoke bootstrap
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

test:
	$(VENV)/pytest -q

up:            ## application + postgres + redis + Ollama
	$(COMPOSE) up --build

up-full:       ## + langfuse
	$(COMPOSE) --profile observability up --build

models:        ## start Ollama and download the local models
	$(COMPOSE) up -d ollama
	$(COMPOSE) exec ollama ollama pull qwen3-embedding:0.6b
	$(COMPOSE) exec ollama ollama pull qwen3:4b

down:
	$(COMPOSE) down

build:          ## rebuild the orchestrator + ingestion images
	$(COMPOSE) build orchestrator ingestion

ingest:        ## offline: chunk docs -> embed -> pgvector
	$(MAKE) models
	$(COMPOSE) run --rm --build ingestion

smoke:          ## end-to-end smoke test: auth -> resolve -> chat against the running stack
	bash scripts/smoke_e2e.sh

eval:          ## run Ragas/DeepEval against docs/reference-answers.json
	$(VENV)/python -m eval.run_eval --gold docs/reference-answers.json
