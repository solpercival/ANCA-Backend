# Offline ingestion job (chunk -> embed -> pgvector).
# Installs the model extras; run on demand, not as a long-lived service.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY ingestion/ ./ingestion/
RUN pip install --no-cache-dir -e ".[models]" && rm -rf /root/.cache
CMD ["python", "-m", "ingestion.pipeline"]
