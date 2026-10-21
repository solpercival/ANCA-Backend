# Offline ingestion job (chunk -> embed -> pgvector).
# Installs the model extras; run on demand, not as a long-lived service.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY ingestion/ ./ingestion/
# the documentation team's repository (the docs/working_docs submodule; make ingest
# checks it out), and from our copy only the alarm catalogue, which adds the alarm
# descriptions retrieval uses (ingestion/seed_alarms.py)
COPY docs/working_docs/ ./docs/working_docs/
COPY docs/docs-proto/starter-kit/alarms/ ./docs/docs-proto/starter-kit/alarms/
RUN pip install --no-cache-dir -e ".[models]" && rm -rf /root/.cache
CMD ["python", "-m", "ingestion.pipeline"]
