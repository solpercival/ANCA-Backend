.PHONY: install lint test up down ingest models eval fmt
VENV=.venv/bin

install:
	python3 -m venv .venv && $(VENV)/pip install -e ".[dev]"

fmt:
	$(VENV)/ruff format . && $(VENV)/ruff check --fix .

lint:
	$(VENV)/ruff check . && $(VENV)/pylint src/rag_engine || true

test:
	$(VENV)/pytest -q

up:            ## light stack: orchestrator + postgres + redis
	docker compose up --build

up-full:       ## + Ollama + langfuse
	docker compose --profile models --profile observability up --build

models:        ## start Ollama and download the local models
	docker compose --profile models up -d ollama
	docker compose --profile models exec ollama ollama pull qwen3-embedding:0.6b
	docker compose --profile models exec ollama ollama pull qwen3:4b

down:
	docker compose down

ingest:        ## offline: chunk docs -> embed -> pgvector + BM25
	$(MAKE) models
	docker compose --profile models run --rm --build ingestion

eval:          ## run Ragas/DeepEval against docs/reference-answers.json
	$(VENV)/python -m eval.run_eval --gold docs/reference-answers.json
