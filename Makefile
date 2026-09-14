.PHONY: install lint test up down ingest models eval fmt
VENV=.venv/bin

install:
	python3.14 -m venv .venv && $(VENV)/pip install -e ".[dev]"

fmt:
	$(VENV)/ruff format . && $(VENV)/ruff check --fix .

lint:
	$(VENV)/ruff check . && $(VENV)/pylint src/rag_engine || true

test:
	$(VENV)/pytest -q

up:            ## application + postgres + redis + Ollama
	docker compose up --build

up-full:       ## + langfuse
	docker compose --profile observability up --build

models:        ## start Ollama and download the local models
	docker compose up -d ollama
	docker compose exec ollama ollama pull qwen3-embedding:0.6b
	docker compose exec ollama ollama pull qwen3:4b

down:
	docker compose down

ingest:        ## offline: chunk docs -> embed -> pgvector
	$(MAKE) models
	docker compose run --rm --build ingestion

eval:          ## run Ragas/DeepEval against docs/reference-answers.json
	$(VENV)/python -m eval.run_eval --gold docs/reference-answers.json
