# Orchestrator / FastAPI service. CPU-only image — no models live here.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY ingestion/ ./ingestion/

RUN pip install --no-cache-dir -e . && rm -rf /root/.cache

EXPOSE 8080
CMD ["uvicorn", "rag_engine.main:app", "--host", "0.0.0.0", "--port", "8080"]
