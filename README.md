# CNC Troubleshooting RAG Engine

Alarm-code-driven troubleshooting assistant: resolve-by-code and conversational
chat over CNC documentation, using hybrid retrieval (pgvector), Ollama
models, FastAPI orchestration, Redis, and PostgreSQL.

## Repository shape

| Repo | Owns | Notes |
|------|------|-------|
| **this repo** | RAG engine + ingestion | docs are a **submodule** at `docs/` |
| `cnc-documentation` (submodule) | source manuals + `reference-answers.json` | documentation team |
| `frontend` (separate repo) | App UI | consumes the `/api/v1` contract |

## Layout

```
src/rag_engine/      FastAPI app, orchestrator, retrieval, generation, auth
  api/               routes, OAuth2 tier auth, request/response schemas
  retrieval/         interfaces (Protocols), hybrid RRF, embedder/reranker/vectorstore
  generation/        response LLM adapter
  stores/            postgres + redis adapters
ingestion/           OFFLINE: chunk -> embed -> pgvector
eval/                Ragas/DeepEval harness vs the gold set
tests/               CPU-only unit tests (no models) — the CI gate
docker/              orchestrator + ingestion images
docker-compose.yml   local stack (optional observability profile)
.github/workflows/   ci.yml (hosted) + eval.yml (GPU, disabled)
```

## Quick start

### Docker Desktop with WSL

When running these commands from WSL, use Docker Desktop's WSL integration:

1. In Docker Desktop, open **Settings > Resources > WSL Integration** and
  enable your Ubuntu distribution.
2. Apply the change and restart Docker Desktop.
3. In Ubuntu, select Docker Desktop's Unix-socket context:

  ```bash
  docker context use default
  docker version
  ```

  `docker version` must show both a Client and Server section. If the WSL
  environment was already open before enabling integration, restart it from
  PowerShell with `wsl --shutdown`, then open Ubuntu again.

Run the remaining commands from the repository directory. In WSL, a Windows
checkout is typically available under `/mnt/c/Users/<your-user>/...`.

```bash
cp .env.example .env
make install          # venv + dev deps (no models)
make test             # unit tests
make up               # orchestrator + PostgreSQL(pgvector) + redis + Ollama
# open http://localhost:8080/docs  (OpenAPI / Swagger)
```

`.env` is for local development and is gitignored. Keep real credentials out of
commits, logs, and container images. Do not use this file as a production
secrets mechanism.

Download the local Ollama models after the stack is running:

```bash
make models
```

Build the offline indexes:

```bash
make ingest           # writes pgvector rows
```

PostgreSQL stores dense vectors

Bring up the stack with Langfuse enabled with:

```bash
make up-full
```

## Design boundaries (who owns what)

- **Documentation team** — the `docs` submodule *and* ingestion: content through
  to a populated, validated index. Deliverable = store contents meeting the
  schema and passing the eval thresholds.
- **RAG team** — everything that *reads* the index: orchestrator, hybrid
  retrieval, reranking, generation, the `/api/v1` contract, and the platform
  layer (compose, CI, auth, Langfuse).
- **Frontend team** — the App UI, in its own repo, against the OpenAPI spec.

## CI/CD

- **`ci.yml`** runs on every push/PR on **hosted runners**: ruff, pylint, mypy,
  pytest, and an image build. It never loads a model — model-backed code sits
  behind `Protocol` interfaces and is faked in tests, which is what keeps CI
  free of GPUs.

### Secrets

Settings load from environment variables (`.env` locally; gitignored,
never committed — see `.env.example` for local examples).

**Secrets:** `JWT_SECRET`, `POSTGRES_PASSWORD`, `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `HF_TOKEN`, `LANGFUSE_SECRET_KEY`.
`LANGFUSE_PUBLIC_KEY` identifies the Langfuse project and isn't
sensitive by design. Everything else (e.g. `LANGFUSE_HOST`) is
plain config, not a credential.

**CI** already injects secrets via GitHub Actions Secrets
(`rag-eval.yml` reads `LANGFUSE_SECRET_KEY`, etc.) — the pattern to
follow for any workflow that needs credentials.

**Production** isn't implemented yet: no deployment or secret
retrieval exists in this repo. Values should eventually come from a
managed secrets store (Vault or another platform-native option) —
backend choice still TBD.

`JWT_SECRET` already fails fast outside `local` if it's the
placeholder or under 32 characters. `POSTGRES_PASSWORD` has no
equivalent guard yet and still defaults to `"rag"` — production
must override it manually until that check exists (tracked as a
follow-up).

## Cloning (submodule!)

```bash
git clone --recurse-submodules git@github.com:your-org/rag-engine.git
# or, after a plain clone:
git submodule update --init --recursive
```
