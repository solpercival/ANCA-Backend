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
                      # (runs the schema migrations first, via the `migrate` service)
# open http://localhost:8080/docs  (OpenAPI / Swagger)
```

Download the local Ollama models after the stack is running:

```bash
make models
```

Build the offline indexes:

```bash
make ingest           # applies migrations, then writes pgvector rows
```

### Database migrations

The schema is versioned with [Alembic](https://alembic.sqlalchemy.org/) in
`migrations/`. The migrations are the only schema definition: there is no SQL
init script, and ingestion doesn't create tables at runtime.
`migrations/env.py` reads the database URL from the app settings
(`POSTGRES_*` in `.env`), so there is no URL to configure.

`make up` and `make ingest` apply pending migrations automatically through the
one-shot `migrate` compose service. To run them yourself:

```bash
make migrate          # alembic upgrade head
make migrate-status   # current revision + history
make migrate-down     # roll back one revision (alembic downgrade -1)
make db-reset         # drop everything and rebuild empty (downgrade base + upgrade head)
```

`make db-reset` deletes all data (ingested chunks, users, the alarm catalogue) and
stops the orchestrator; run `make ingest && make restart` afterwards. New
revisions: `make revision m="short description"`. Don't reset by dropping tables by hand: that
leaves Alembic's `alembic_version` row behind, and `upgrade head` then creates
nothing.

From the host venv instead of Docker, point it at the published port:

```bash
POSTGRES_HOST=localhost .venv/bin/alembic upgrade head
POSTGRES_HOST=localhost .venv/bin/alembic downgrade -1     # one step back
POSTGRES_HOST=localhost .venv/bin/alembic downgrade base   # drop everything (dev only)
POSTGRES_HOST=localhost .venv/bin/alembic upgrade head --sql   # print SQL, don't run it
```

**Changing the schema:** add a new revision rather than editing an existing
one. Revision `0001` is a copy of the former `scripts/init_pgvector.sql` init
script (still in git history) and must stay that way.

```bash
.venv/bin/alembic revision -m "add response.rating"   # then write upgrade()/downgrade()
```

**Existing databases** created by the old init script already have the 0001
schema. Mark them as migrated once, instead of upgrading:

```bash
make migrate-status                                         # "current" is empty
docker compose run --rm migrate alembic stamp 0001          # record 0001 as applied
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
- **`eval.yml`** is **disabled** until a self-hosted GPU runner exists. It loads
  the real models and scores the engine against `docs/reference-answers.json`.

## Cloning (submodule!)

```bash
git clone --recurse-submodules git@github.com:your-org/rag-engine.git
# or, after a plain clone:
git submodule update --init --recursive
```
