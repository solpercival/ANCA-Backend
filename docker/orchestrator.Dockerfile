# Orchestrator / FastAPI service.
# By default installs the `models` extra (torch + transformers) so the Qwen3
# reranker can run in-process on the GPU (see docker-compose.gpu.yml). For a slim
# CPU-only image with RERANK_PROVIDER=none, build with --build-arg EXTRAS=
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

ARG EXTRAS=models
# torch's CUDA build must not be newer than the host driver supports, or CUDA
# silently fails to initialise and the reranker falls back to CPU. PyPI's default
# wheel is now CUDA 13 (driver >= 580); cu126 runs on drivers >= 560 (12.6+).
# Check the host with `nvidia-smi` ("CUDA Version") and override if needed.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu126

# Heavy model deps get their own layer *before* the source is copied, so a code
# change doesn't reinstall torch (several GB). Keep in step with pyproject's extra.
RUN if [ "$EXTRAS" = "models" ]; then \
        pip install --no-cache-dir --index-url "$TORCH_INDEX_URL" "torch>=2.5" \
        && pip install --no-cache-dir "sentence-transformers>=3.3" \
        && rm -rf /root/.cache; \
    fi

# gcc/libc6-dev: Triton (bundled with torch) JIT-builds a small CUDA launcher on the
# first GPU forward pass and fails with "Failed to find C compiler" without one.
# curl: used by the compose healthcheck (GET /ready).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
       $(if [ "$EXTRAS" = "models" ]; then echo gcc libc6-dev; fi) \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
COPY ingestion/ ./ingestion/

RUN if [ -n "$EXTRAS" ]; then pip install --no-cache-dir -e ".[$EXTRAS]"; \
    else pip install --no-cache-dir -e .; fi && rm -rf /root/.cache

EXPOSE 8080
CMD ["uvicorn", "rag_engine.main:app", "--host", "0.0.0.0", "--port", "8080"]
