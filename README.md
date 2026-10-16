# CNC Troubleshooting RAG Engine

Alarm-code-driven troubleshooting assistant: resolve-by-code and conversational
chat over CNC documentation, using hybrid retrieval (pgvector), Ollama
models, FastAPI orchestration, Redis, and PostgreSQL.

## Repository shape

| Repo | Owns | Notes |
|------|------|-------|
| **this repo** | RAG engine + ingestion | docs are a **submodule** at `docs/` |
| `cnc-documentation` (submodule) | source manuals + `reference-answers.json` | documentation team |
| `frontend` (separate repo) | App UI | consumes the HTTP API contract ([Frontend integration](#frontend-integration-api-contract)) |

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

  Server must say `Docker Desktop` (`docker info | grep "Operating System"`).
  If Ubuntu has its own Docker engine installed as well (`docker.io` or
  `docker-ce`), `default` reaches that empty engine whenever Docker Desktop is
  not running, and the stack appears to have lost its images and data. Stop it
  with `sudo systemctl disable --now docker docker.socket`.

Run the remaining commands from the repository directory. In WSL, a Windows
checkout is typically available under `/mnt/c/Users/<your-user>/...`.

```bash
cp .env.example .env
make help             # list all make targets with a one-line description
make install          # venv + dev deps (no models)
make test             # unit tests
make up               # orchestrator + PostgreSQL(pgvector) + redis + Ollama
                      # (runs the schema migrations first, via the `migrate` service)
# open http://localhost:8080/docs  (OpenAPI / Swagger)
```

`.env` is for local development and is gitignored. Keep real credentials out of
commits, logs, and container images. Do not use this file as a production
secrets mechanism.

Download the local Ollama models after the stack is running:

```bash
make models
```

The default generator is `qwen3:8b` (about 5 GB to download, about 6 GB of GPU
memory). On a GPU with less memory, set
`LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M` in `.env` and `ollama pull` it. It
scores lower on the eval (see `.env.example`).

Build the offline indexes:

```bash
make ingest           # applies migrations, then writes pgvector rows
```

Run `make reingest` instead after changing the chunker or `EMBEDDING_SETUP`, and
before an eval run you want to compare with others. An index left from an
earlier build retrieves the same documents with different chunk text, and that
moved `fix_solved` by a whole fix (`eval/results/ladder/README.md`).

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

## Frontend integration (API contract)

Locally the API is at `http://localhost:8080`, and the live, always-current
schema is at `http://localhost:8080/docs` (Swagger) and `/openapi.json`. This
section is the summary plus the behaviour the schema can't show.

**Base path.** Every endpoint lives under `/api/<version>`. The paths below are
written relative to that base, so `POST /resolve` means
`POST http://localhost:8080/api/<version>/resolve`. The current version is
**`v2`**. Keep the base in one constant in the client (see
[Minimal client](#minimal-client)), so a version change is a one-line edit.

### Conventions

- **JSON** request and response bodies, except login, which is form-encoded.
- **Auth:** send `Authorization: Bearer <access_token>` on every call except
  login, refresh, logout, health and ready. With `ALLOW_ANONYMOUS_OPERATOR=true`,
  `/resolve` and `/feedback` also accept a call with no `Authorization` header and
  treat it as an operator. A token that is sent must be valid: an expired or
  malformed one is a `401`, never an anonymous call.
- **Request id:** every response carries `X-Request-ID`. Send your own
  `X-Request-ID` to choose it; otherwise one is generated. Show it in error
  messages so a report can be matched to the server logs.
- **Body limit:** 64 KiB per request (`413 payload_too_large` above that).
- **CORS:** allowed origins are `CORS_ALLOW_ORIGINS` (default
  `http://localhost:3000`, `http://127.0.0.1:3000`, and the Vite dev server on
  `http://localhost:5173` and `http://127.0.0.1:5173`). Credentials are allowed,
  so the origin must match exactly. Add your dev or deployed origin there.
- **Slow calls:** `/resolve` and `/chat` wait for an LLM and can take from a
  few seconds to tens of seconds. Show a loading state and don't use a short
  client timeout. Responses are not streamed.

### Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/auth/token` | none | Log in |
| POST | `/auth/refresh` | refresh cookie | New access token |
| POST | `/auth/logout` | refresh cookie | End this session |
| POST | `/auth/logout-all` | bearer | End every session of the account |
| GET | `/auth/me` | bearer | Current account |
| POST | `/resolve` | bearer, or none as an operator (`ALLOW_ANONYMOUS_OPERATOR`) | Guidance for an alarm code |
| POST | `/chat` | bearer, technician or partner | Follow-up question |
| POST | `/feedback` | bearer (any tier), or none as an operator (`ALLOW_ANONYMOUS_OPERATOR`) | Mark a chat reply or resolve answer as helpful or not |
| GET | `/health` | none | Process is up |
| GET | `/ready` | none | Postgres, Redis and model server reachable |

### Authentication flow

1. **Log in.** `POST /auth/token` with a form body
   (`Content-Type: application/x-www-form-urlencoded`): `username=...&password=...`.

   ```json
   { "access_token": "<jwt>", "token_type": "bearer", "expires_in": 900 }
   ```

   The response also sets a `refresh_token` cookie (HttpOnly, sent only to the
   `/auth` endpoints). JavaScript can't read it and doesn't need to.
2. **Call the API** with the access token in the `Authorization` header. Keep
   the token in memory, not in `localStorage`.
3. **Refresh.** The access token lasts `expires_in` seconds (15 minutes by
   default; the sample `.env` sets 60). Before it expires, or on a `401 unauthorized`, call
   `POST /auth/refresh` with no body. It returns the same shape as login
   and rotates the cookie.
4. **Log out.** `POST /auth/logout` returns `204` and clears the cookie.

Rules that matter in the browser:

- Calls to `/auth/*` must send cookies: `fetch(url, { credentials: "include" })`
  or `axios` with `withCredentials: true`. Without it, login appears to work but
  refresh always fails.
- On page load there is no access token in memory. Call `/auth/refresh` first;
  if it returns `401`, show the login screen.
- If two refreshes race (two tabs, or a retry), the loser gets
  `401 unauthorized` with the message "Session was refreshed by another
  request; retry". Retry the refresh once.
- `401 session_expired` means the session is over: send the user to login.
- The cookie is `Secure` by default. Browsers accept that on
  `http://localhost`; if yours doesn't store it over plain HTTP, set
  `AUTH_COOKIE_SECURE=false` in the backend `.env` for local development only.
- Login is rate limited: 5 failures per username and 20 per IP in 15 minutes,
  then `429 rate_limited` with a `Retry-After` header (seconds).

`GET /auth/me` returns the account, for showing the user and deciding
what to render:

```json
{ "user_id": 1, "username": "alex", "tier": "technician" }
```

There is no sign-up endpoint. To create a local test user, with the stack up:

```bash
POSTGRES_HOST=localhost .venv/bin/python - <<'PY'
import asyncio
from rag_engine.auth import passwords
from rag_engine.auth.tiers import Tier
from rag_engine.auth.user_repository import PostgresUserRepository
from rag_engine.stores.db import init_db_pool

async def main():
    init_db_pool()
    pw_hash = await passwords.hash_password("s3cret-pw!")
    await PostgresUserRepository().create("alex", pw_hash, Tier.technician)

asyncio.run(main())
PY
```

### Tiers

| Tier | `/resolve` | `likely_causes` | `/chat` | Answers drawn from |
|------|-----------|-----------------|---------|--------------------|
| `operator` | yes | always `[]` | `403 forbidden` | Part Programmer's Reference only |
| `technician` | yes | shown | yes | all docs (incl. User Guide) |
| `partner` | yes | shown | yes | all docs (incl. User Guide) |

The documentation restriction is a query-time filter on the document path
(`auth/tiers.py` `allowed_doc_audiences`), so an operator resolve for an alarm
documented only in the User Guide returns `doc_coverage: "none"` and no citations.

Use `ai_chat_available` from the resolve response (or `tier` from `/auth/me`)
to decide whether to show the chat entry point, rather than hard-coding tier
names.

### POST /resolve

Open to every tier. With `ALLOW_ANONYMOUS_OPERATOR=true`, a call with no
`Authorization` header gets the operator view: `likely_causes` is `[]`,
`ai_chat_available` is `false`, and the escalation fields are set as for an
operator. Anonymous calls count against the per-IP rate limit like any other.

Request:

```json
{
  "code": "am.fb.0002",
  "env": { "versions": { "amcore": "1.4.2" }, "machine_variant": "MX7" },
  "effort": "medium",
  "query": "happens after a tool change",
  "conversation_id": "c-7f3a"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `code` | yes | Lowercase `<origin>.<module>.<sequence>`, e.g. `am.fb.0002`; must match `^[a-z]{2,4}\.[a-z]{2,6}\.\d{4}$` |
| `env` | no | Machine context; narrows the documentation searched. Omit if unknown |
| `effort` | no | `low`, `medium` (default) or `high`; higher is slower and more thorough |
| `query` | no | Free-text symptom, up to 1000 characters |
| `conversation_id` | no | 1-128 characters. Records the answer under that conversation, so a later `/chat` message with the same id can refer back to it, and returns a `response_id` for `/feedback` |

Response `200`:

```json
{
  "code": "am.fb.0002",
  "title": "Drive emergency (EMCY)",
  "domain": "Fieldbus",
  "severity": 833,
  "severity_category": "Error",
  "steps": ["Check the drive's emergency error code in the device diagnostics."],
  "doc_coverage": "partial",
  "likely_causes": ["A device sends an emergency message when it detects an internal error."],
  "citations": [
    {
      "doc": "AMCore User Guide",
      "path": "user-guide/troubleshoot/coe-device-errors.md",
      "section": "Emergency Error"
    }
  ],
  "tier": "technician",
  "ai_chat_available": true,
  "safety_note": null,
  "escalation_suggested": false,
  "escalation_note": null,
  "confidence": 0.5,
  "response_id": 4821
}
```

| Field | Meaning |
|-------|---------|
| `title`, `domain`, `severity` (1-1000), `severity_category` | The alarm header from the catalogue. Display only; it is not guidance |
| `steps` | The guidance, one point per element, already cleaned of numbering. Render as a list |
| `doc_coverage` | `full`: the docs give explicit steps. `partial`: the docs explain the alarm but give no complete fix. `none`: the docs don't cover it |
| `likely_causes` | Up to 3 sentences taken from the documentation; often empty |
| `citations` | Up to 3 documentation sections the answer drew on. `doc` is the document's display name, `path` is relative to the documentation root (link to it), `section` is the heading the text sits under, or `null` if it has none |
| `confidence` | Derived from `doc_coverage` (0.9, 0.5, 0.0). Use `doc_coverage` for UI decisions |
| `safety_note` | A verify-before-acting caution, set for safety-related alarms (`severity_category` `Fatal` by default; `SAFETY_SEVERITY_CATEGORIES`) for every tier, otherwise `null`. Show it prominently with the steps |
| `escalation_suggested`, `escalation_note` | `true` with a message for an operator when the alarm is safety-related or `doc_coverage` is `none`/`partial`: prompt them to escalate. Always `false`/`null` for technician and partner |
| `response_id` | Identifies this answer for `POST /feedback`. Set only when the request gave a `conversation_id` (feedback is addressed by both); otherwise `null` |

When `doc_coverage` is `none`, `steps` holds the single line "The documentation
does not cover this alarm." and `likely_causes` is empty. Show that state
differently from a real answer, for example with an escalation prompt.

An unknown but well-formed code returns `404 unknown_alarm_code`; a malformed
one returns `422 validation_error`.

### POST /chat

Request:

```json
{ "conversation_id": "c-7f3a", "message": "What if the restart doesn't clear it?", "effort": "medium" }
```

`conversation_id` is chosen by the client (1-128 characters, for example a
UUID). Reuse it to continue a conversation; a new id starts a new one.
`message` is 1-4096 characters.

Response `200`:

```json
{
  "conversation_id": "c-7f3a",
  "reply": "Check the device's EMCY code in the diagnostics view ...",
  "citations": [
    {
      "doc": "AMCore User Guide",
      "path": "user-guide/troubleshoot/coe-device-errors.md",
      "section": "Emergency Error"
    }
  ]
}
```

`reply` is plain text and may contain line breaks. `response_id` identifies
this reply for `POST /feedback`; it is `null` when nothing was stored (an empty
message gets an empty reply and no id).

### POST /feedback

The "this did not help" button, for a `/chat` reply or a `/resolve` answer. Use
the `response_id` and `conversation_id` that call returned. Open to every tier,
and to anonymous operators when `ALLOW_ANONYMOUS_OPERATOR=true`. Request:

```json
{ "conversation_id": "c-7f3a", "response_id": 4821, "helpful": false }
```

Response `204` with no body. Sending feedback again for the same reply
replaces the earlier value. The next `/chat` message in the conversation passes
it to the query rewriter, which treats a reply marked `helpful: false` as one
that was tried and failed.

A `response_id` that doesn't exist, or doesn't belong to `conversation_id`,
returns `404 not_found`.

### Errors

Every error, from any endpoint, has this body:

```json
{
  "error": {
    "code": "unknown_alarm_code",
    "message": "Alarm code not found",
    "request_id": "9f2c...",
    "details": []
  }
}
```

Branch on `error.code`, never on `message` (messages may be reworded).
`details` is filled for validation errors as `[{ "field": "code", "message": "..." }]`.

| Status | `code` | What the UI should do |
|--------|--------|-----------------------|
| 401 | `unauthorized` | Refresh the token once, then retry the call |
| 401 | `invalid_credentials` | Wrong username or password |
| 401 | `session_expired` | Send the user to login |
| 403 | `forbidden` | The tier can't use this feature; hide it |
| 404 | `unknown_alarm_code` | Tell the user the code isn't recognised |
| 404 | `not_found` | Wrong URL, or `/feedback` for a reply that isn't in the conversation |
| 413 | `payload_too_large` | Input too long |
| 422 | `validation_error` | Show `details` next to the fields |
| 429 | `rate_limited` | Wait `Retry-After` seconds before retrying |
| 503 | `retrieval_unavailable`, `model_unavailable`, `auth_unavailable`, `rate_limit_unavailable` | Temporary; offer a retry |
| 504 | `upstream_timeout` | Temporary; offer a retry |
| 500 | `internal_error` | Show a generic failure with the request id |

Rate limits on the business endpoints, per minute: `/resolve` 30 per IP,
`/chat` 10 per IP, `/feedback` 30 per IP (each plus a shared per-tier
ceiling). All are configurable in the backend `.env`.

### Minimal client

```js
const API_VERSION = "v2"; // the only place the version appears
const API = `http://localhost:8080/api/${API_VERSION}`;
let accessToken = null;

async function login(username, password) {
  const res = await fetch(`${API}/auth/token`, {
    method: "POST",
    credentials: "include",
    body: new URLSearchParams({ username, password }),
  });
  if (!res.ok) throw (await res.json()).error;
  accessToken = (await res.json()).access_token;
}

async function refresh() {
  const res = await fetch(`${API}/auth/refresh`, { method: "POST", credentials: "include" });
  if (!res.ok) { accessToken = null; return false; }
  accessToken = (await res.json()).access_token;
  return true;
}

async function api(path, body, retried = false) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(body),
  });
  if (res.status === 401 && !retried && (await refresh())) return api(path, body, true);
  if (!res.ok) throw (await res.json()).error; // { code, message, request_id, details }
  return res.json();
}

const answer = await api("/resolve", { code: "am.fb.0002" });
```

### Checking the backend is up

`GET /ready` returns `200 {"status": "ok", "checks": {...}}` when
Postgres, Redis and the model server all answer, and `503` with
`"status": "not_ready"` and the same `checks` object otherwise, so you can see
which dependency is down. `scripts/smoke_e2e.sh` runs a login, a resolve and a
chat against a running stack and is a working reference for the calls above.

### Behind HTTPS

The orchestrator serves plain HTTP on 8080 and expects HTTPS to be handled by a
reverse proxy in front of it. It reads the client IP and scheme from the proxy's
`X-Forwarded-For` and `X-Forwarded-Proto` headers, but only from the addresses
in `FORWARDED_ALLOW_IPS`. Set that to your proxy's address, or HSTS is never sent
and every caller shares the proxy's per-IP rate limit.

`make https` tests this locally. It starts Caddy with a certificate from its own
local CA (`docker-compose.https.yml`), serving the API on
`https://localhost:8443` and redirecting `http://localhost:8081`, then runs
`scripts/https_check.sh`. That script checks:

- the certificate and HSTS;
- the HTTP redirect;
- the `Secure` refresh cookie, and refresh over HTTPS;
- that the orchestrator sees the real client IP;
- that a direct caller on 8080 can't fake the forwarded headers;
- `ALLOWED_HOSTS`, if it is set.

For a browser, trust Caddy's root certificate, which
`docker compose -f docker-compose.yml -f docker-compose.https.yml cp caddy:/data/caddy/pki/authorities/local/root.crt .`
copies out. Then add your `https://` front-end origin to `CORS_ALLOW_ORIGINS`.
`make restart` goes back to the plain stack.

### Public access with Tailscale Funnel

This is how the Vercel front end reaches the engine on the GPU machine. The app
proxies `/api/v2/*` through its own domain (a rewrite in the front end's
`frontend/vercel.json`) to
`https://<TS_HOSTNAME>.<tailnet>.ts.net/api/v2/*`. Browsers only ever talk to the
app's domain, so the refresh cookie stays first-party, and Safari keeps the login.

`docker-compose.funnel.yml` runs Tailscale as a container in the stack. It joins
the tailnet as its own machine (`anca-api` by default) and serves that URL to the
internet over Funnel, proxying to the orchestrator on the compose network.
Nothing is published on the host for it, and the orchestrator trusts forwarded
headers only from that container.

**Once, in the Tailscale admin console:**

1. DNS: enable HTTPS certificates.
2. Access controls: allow Funnel for the tag, in the policy file:
   ```json
   "tagOwners": { "tag:anca-api": ["autogroup:admin"] },
   "nodeAttrs": [ { "target": ["tag:anca-api"], "attr": ["funnel"] } ]
   ```
3. Settings → Keys: generate a reusable auth key with the tag `tag:anca-api`, and
   put it in `.env` as `TS_AUTHKEY`.

**`.env` on the GPU machine.** The API becomes reachable by anyone with the URL,
so the placeholder secrets must go:

```env
APP_ENV=production                 # the orchestrator then refuses placeholder secrets
JWT_SECRET=<python3 -c "import secrets; print(secrets.token_urlsafe(48))">
POSTGRES_PASSWORD=<new password, see below>
ALLOWED_HOSTS='["anca-api.<tailnet>.ts.net","localhost"]'   # localhost: the health check
CORS_ALLOW_ORIGINS='["https://<app>.vercel.app"]'           # checked on /auth/refresh
ALLOW_ANONYMOUS_OPERATOR=true      # the front end lets operators in without a login
RESOLVE_RATE_LIMIT_PER_IP=120      # every request arrives from a Vercel server (below)
```

To change the password of a database that already exists, run this, then set the
same value as `POSTGRES_PASSWORD`:
`docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "ALTER USER <POSTGRES_USER> PASSWORD '<new>'"`.
A new `JWT_SECRET` logs everyone out once.

**Run it.** `make funnel`:

1. refuses to start while `APP_ENV` is `local` or a secret is a placeholder;
2. brings up the orchestrator and the Tailscale container;
3. runs `scripts/funnel_check.sh`, which checks:
   - the public URL and HSTS;
   - that the orchestrator sees the real client IP;
   - `/resolve` without a token;
   - that a caller on port 8080 cannot fake forwarded headers;
   - `ALLOWED_HOSTS`.

`make funnel-off` stops the Tailscale container, and the API is no longer
public. `make restart` alone leaves it running.

**For the front end:**

- Set the rewrite destination in `vercel.json` to
  `https://anca-api.<tailnet>.ts.net/api/v2/:path*`.
- Set `VITE_ENGINE_MODE=live`, and leave `VITE_ENGINE_BASE_URL` unset.

**Behaviour to expect:**

- Rate limits are counted per Vercel server, not per phone, because the rewrite
  makes Vercel the client. That is why the per-IP limit above is higher. The
  per-tier limit still applies.
- Login works only on origins listed in `CORS_ALLOW_ORIGINS`. Vercel preview
  deployments have their own URLs, so on a preview only the no-login operator
  view works.
- The first answer after a restart takes about 17 s while the models load. Open
  the app once before a demo. The machine must stay on, with Docker Desktop
  running.

## Design boundaries (who owns what)

- **Documentation team** — the `docs` submodule *and* ingestion: content through
  to a populated, validated index. Deliverable = store contents meeting the
  schema and passing the eval thresholds.
- **RAG team** — everything that *reads* the index: orchestrator, hybrid
  retrieval, reranking, generation, the HTTP API contract, and the platform
  layer (compose, CI, auth, Langfuse).
- **Frontend team** — the App UI, in its own repo, against the OpenAPI spec.

## CI/CD

- **`ci.yml`** runs on every push/PR on **hosted runners**: ruff, pylint, mypy,
  pytest, and an image build. It never loads a model. Model-backed code sits
  behind `Protocol` interfaces and is faked in tests, which is what keeps CI
  free of GPUs.

### Secrets

Settings load from environment variables (`.env` locally; gitignored,
never committed, see `.env.example` for local examples).

**Secrets:** `JWT_SECRET`, `POSTGRES_PASSWORD`, `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `HF_TOKEN`, `LANGFUSE_SECRET_KEY`.
`LANGFUSE_PUBLIC_KEY` identifies the Langfuse project and isn't
sensitive by design. Everything else (e.g. `LANGFUSE_HOST`) is
plain config, not a credential.

**CI** already injects secrets via GitHub Actions Secrets
(`rag-eval.yml` reads `LANGFUSE_SECRET_KEY`, etc.) -> the pattern to
follow for any workflow that needs credentials.

**Production** isn't implemented yet: no deployment or secret
retrieval exists in this repo. Values should eventually come from a
managed secrets store (Vault or another platform-native option)
backend choice still TBD.

`JWT_SECRET` already fails fast outside `local` if it's the
placeholder or under 32 characters. `POSTGRES_PASSWORD` has no
equivalent minimum-length check, but now rejects blank values and the
known placeholders (`"rag"` and `"change_in_prod"`) outside `local`.
Production must set a non-placeholder password.

## Cloning (submodule!)

```bash
git clone --recurse-submodules git@github.com:your-org/rag-engine.git
# or, after a plain clone:
git submodule update --init --recursive
```
