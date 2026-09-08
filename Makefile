.PHONY: install lint test up down ingest eval fmt
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

up-full:       ## + model servers (needs GPU) + langfuse
	docker compose --profile models --profile observability up --build

down:
	docker compose down

ingest:        ## offline: chunk docs -> embed -> pgvector + BM25
	docker compose run --rm --build -f docker/ingestion.Dockerfile ingestion

eval:          ## run Ragas/DeepEval against docs/reference-answers.json
	$(VENV)/python -m eval.run_eval --gold docs/reference-answers.json
