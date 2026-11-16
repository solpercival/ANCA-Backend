# CNC Troubleshooting RAG Engine

The backend of the alarm troubleshooting assistant. Given an alarm code such as
`am.fb.0002`, it finds the relevant sections of the AMCore documentation and
answers with the steps to clear the alarm. Technicians and partners can also ask
follow-up questions in a chat.

It runs as one Docker Compose stack on a machine with an NVIDIA GPU:

- a FastAPI **orchestrator** (the API, on port 8080);
- **PostgreSQL** with pgvector, for the document chunks, the alarm catalogue,
  accounts and conversations;
- **Redis**, for login sessions and rate limits;
- **Ollama**, for the embedding model and the answer model (`qwen3:8b`).

The Vercel front end reaches it over HTTPS through a Tailscale Funnel.

## Contents

1. [Set up a new instance](#set-up-a-new-instance): start to finish
2. [Running it day to day](#running-it-day-to-day)
3. [Troubleshooting](#troubleshooting)
4. [How it works](#how-it-works)
5. [Configuration](#configuration)
6. [Documentation and ingestion](#documentation-and-ingestion)
7. [Database migrations](#database-migrations)
8. [Frontend integration (API contract)](#frontend-integration-api-contract)
9. [Deployment: HTTPS and public access](#deployment-https-and-public-access)
10. [Evaluation](#evaluation)
11. [Development](#development)

## Set up a new instance

Follow the steps in order. Steps 1 to 6 give a working instance on
`http://localhost:8080`. Step 7 makes it reachable by the Vercel front end.

### What you need

- Windows 11 with WSL 2 (Ubuntu) and Docker Desktop, or Linux with Docker
  Engine and the NVIDIA Container Toolkit.
- An NVIDIA GPU with at least 8 GB of memory and a current driver (development
  used an RTX 4070). It also runs without a GPU, but each answer takes far longer.
- In WSL or Linux: `git`, `make`, `curl` and Python 3.12:
  `sudo apt install git make curl python3.12 python3.12-venv`.
- Disk space for the images and about 7 GB of models.
- For step 7 only: admin access to a Tailscale tailnet.

Run every command below in the WSL (Ubuntu) terminal, from the repository folder.

### 1. Docker Desktop with WSL

1. In Docker Desktop, open **Settings > Resources > WSL Integration**, enable
   your Ubuntu distribution, apply, and restart Docker Desktop.
2. In Ubuntu, check that Docker Desktop answers:

   ```bash
   docker context use default
   docker info | grep "Operating System"     # must say Docker Desktop
   ```

   If Ubuntu was already open, restart it first: run `wsl --shutdown` in
   PowerShell, then open Ubuntu again.
3. If Ubuntu also has its own Docker engine (`docker.io` or `docker-ce`), turn it
   off: `sudo systemctl disable --now docker docker.socket`. Otherwise, whenever
   Docker Desktop is not running, commands reach that empty engine and the stack
   seems to have lost its images and data.
4. In Docker Desktop, turn on **Settings > General > Start Docker Desktop when
   you sign in**, so the stack comes back after a reboot.

### 2. Get the code

```bash
git clone --recurse-submodules <repo-url> ANCA-Backend
cd ANCA-Backend
```

The documentation is a git submodule in `docs/working_docs`. If you cloned
without `--recurse-submodules`, run `git submodule update --init --recursive`
(`make ingest` also does this). A Windows folder works too: in WSL,
`C:\Users\<you>\...` is `/mnt/c/Users/<you>/...`.

### 3. Create `.env`

```bash
cp .env.example .env
```

The defaults work for a local instance. `.env` holds the secrets, is gitignored,
and must never be committed.

**If this machine will be public (step 7), set the production values from
[step 7](#7-make-it-public-for-the-vercel-front-end) now.** Postgres fixes its
password when it first starts, so changing `POSTGRES_PASSWORD` later takes an
extra command.

### 4. Install the Python tools and run the tests

```bash
make install     # .venv with the project and dev tools (the models run in containers)
make test        # unit tests; no services needed, about 4 minutes
```

`make user`, `make smoke` and `make eval` also use this `.venv`.

### 5. Start the stack and load the documentation

```bash
make up          # terminal 1: builds the images, runs the stack in the foreground
make ingest      # terminal 2: migrations, model downloads (~6 GB), then embeds the docs
```

`make up` stays in the foreground, and Ctrl+C stops it. To run the stack in the
background instead, use `make restart` (or `make funnel` in step 7). Always start
it through `make`: a plain `docker compose up` leaves out the GPU.

Check it:

```bash
curl http://localhost:8080/api/v2/ready  # {"status":"ok",...} once Postgres, Redis and Ollama answer
make smoke                               # log in -> resolve -> chat, with a temporary account
```

The interactive API docs are at `http://localhost:8080/docs`.

### 6. Create accounts

There is no sign-up. Operators need no account when `ALLOW_ANONYMOUS_OPERATOR=true`
(the front end lets them in without a login). Technicians and partners need one:

```bash
make user u=alex tier=technician     # asks for the password twice, at least 12 characters
make user u=alex tier=partner        # run again to change the tier or password; reactivates it
make user-disable u=alex             # the account can no longer log in
```

See [Tiers](#tiers) for what each tier can do. Usernames are stored in lower case.

`make smoke` deletes its test account when it finishes. `make eval` keeps a
technician account, `evaluser`, with the password `EVAL_PASSWORD`, and the default
for that is in this repository. On a public instance, set `EVAL_PASSWORD` in
`.env` to a private value before running `make eval`. If the account already has
the default password, run `make user-disable u=evaluser`. Run
`make user u=evaluser tier=technician` to turn it back on before the next eval.

### 7. Make it public for the Vercel front end

The front end proxies `/api/v2/*` to this machine through a Tailscale Funnel.
The full explanation is in
[Public access with Tailscale Funnel](#public-access-with-tailscale-funnel). In
short:

1. **Once, in the Tailscale admin console:** enable HTTPS certificates, and allow
   Funnel for `tag:anca-api` in the access-control policy.
2. **Production values in `.env`:**

   ```env
   APP_ENV=production
   JWT_SECRET=<python3 -c "import secrets; print(secrets.token_urlsafe(48))">
   POSTGRES_PASSWORD=<a new password>
   ALLOWED_HOSTS='["anca-api.<tailnet>.ts.net","localhost"]'
   CORS_ALLOW_ORIGINS='["https://<app>.vercel.app"]'
   ALLOW_ANONYMOUS_OPERATOR=true
   RESOLVE_RATE_LIMIT_PER_IP=120
   ```

   `CORS_ALLOW_ORIGINS` is the front end's exact origin. Login only works from it.
3. **Join the tailnet, once:** `make funnel-login`, then open the printed
   `login.tailscale.com` link and approve the machine. Alternatively, put an
   auth key in `TS_AUTHKEY`.
4. **Go public:** `make funnel`. It refuses to start on placeholder secrets,
   starts the stack in the background with the Funnel, and checks the public URL,
   the GPU and the security settings. Every line should say `PASS`. It prints the
   public URL, `https://anca-api.<tailnet>.ts.net`.
5. **Front end:** in its `vercel.json`, set the rewrite destination to
   `https://anca-api.<tailnet>.ts.net/api/v2/:path*`, and set
   `VITE_ENGINE_MODE=live`.
6. **Test from outside the tailnet**, for example a phone on mobile data. This
   machine and other tailnet devices take a private route to the URL, so they
   can work while the public one does not.

## Running it day to day

| To | Run |
|----|-----|
| Start everything and make it public | `make funnel` |
| Start everything, local only | `make restart` (background) or `make up` (foreground) |
| Stop public access, keep the stack running | `make funnel-off` |
| Stop everything (data is kept) | `make funnel-off`, then `make down` |
| Recover after a reboot | Nothing, once Docker Desktop is running. `make funnel` checks it, and repairs it if needed |
| Apply a code change | `make restart`, or `make retest` for tests, a restart, the benchmark and the eval |
| Apply a documentation change | `make ingest` ([Documentation and ingestion](#documentation-and-ingestion)) |
| Add, change or disable an account | `make user u=<name> tier=<tier>`, `make user-disable u=<name>` |
| Check it answers | `make smoke`, or `make bench` for latency per stage |
| Read the logs | `docker compose logs -f orchestrator` |
| List every target | `make help` |

Under `make funnel`, Ollama keeps the models loaded, so a warm answer takes about
1 to 3 seconds. The first answer after a restart can take up to about 2 minutes
while the models load, so open the app once before a demo.

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| The stack seems to have lost its images and data | WSL reached Ubuntu's own empty Docker engine because Docker Desktop is not running. Start Docker Desktop. See [step 1](#1-docker-desktop-with-wsl) |
| Answers are very slow; `make funnel` fails "has the GPU" | The containers were recreated without the GPU, for example by a plain `docker compose` command. Run `make funnel`, or `make restart` |
| The app works on this PC but not on a phone | The public DNS record for the Funnel can disappear for a while after a restart. Check with `curl "https://dns.google/resolve?name=anca-api.<tailnet>.ts.net&type=A"`. Turning the Funnel off and on (`make funnel-off`, then `make funnel`) brought it back |
| The app shows HTTP 502 just after a restart | The models are still loading. Wait a minute and retry |
| Login returns 429 | 5 failed logins for a username, or 20 from one IP, in 15 minutes. Wait 15 minutes, or clear the counters: `docker compose exec -T redis redis-cli --scan --pattern 'auth:rl:*' \| xargs -r docker compose exec -T redis redis-cli del` |
| Login fails only on a Vercel preview deployment | Previews have their own URLs, which are not in `CORS_ALLOW_ORIGINS`. Only the operator view without a login works there |
| `make funnel` prints a `login.tailscale.com` link and waits | The Tailscale container has not joined the tailnet. Approve the link, or set `TS_AUTHKEY` |

## How it works

`POST /resolve` with an alarm code:

1. Looks up the alarm in the catalogue (its title and description).
2. Embeds the title and description, and retrieves the 50 closest documentation
   chunks from pgvector. Operators only search the Part Programmer's Reference.
   Technicians and partners also search the User Guide.
3. The Qwen3 reranker scores those chunks, and the best 8 are kept, each widened
   to its whole section.
4. `qwen3:8b` writes the steps from those sections only. Steps whose words are
   not in the sections are dropped, and an alarm the documentation does not
   cover gets "not covered" without a model call.

`POST /chat` does the same for a free-text question. It first rewrites a
follow-up into a standalone question, using the conversation, and looks up any
alarm code the question names. Quality, the scores and the known gaps are in
[docs/answer-quality.md](docs/answer-quality.md).

### Repository layout

```
src/rag_engine/      FastAPI app, orchestrator, retrieval, generation, auth
  api/               routes, request/response schemas, errors, rate limiting
  auth/              login, JWT + Redis refresh sessions, tier access checks
  retrieval/         interfaces (Protocols), hybrid RRF, embedder/reranker/vectorstore
  generation/        response LLM adapter
  stores/            postgres + redis adapters
ingestion/           OFFLINE: chunk -> embed -> pgvector
migrations/          Alembic schema revisions
eval/                scores answers against the gold reference answers
scripts/             bootstrap, smoke, bench, eval, HTTPS/Funnel checks, accounts
tests/               CPU-only unit tests (no models): the CI gate
docker/              orchestrator + ingestion images, Tailscale serve config
docs/                working_docs (submodule), docs-proto, design notes
docker-compose*.yml  the stack, plus GPU, HTTPS and Funnel overrides
.github/workflows/   ci.yml (hosted) + eval.yml (GPU, disabled)
```

### Who owns what

| Team | Owns |
|------|------|
| Documentation team | The documentation (the `docs/working_docs` submodule) and its quality: content through to a populated index that passes the eval |
| RAG team (this repo) | Everything that reads the index: orchestrator, retrieval, reranking, generation, the HTTP API contract, and the platform (compose, CI, auth) |
| Frontend team | The app UI, in its own repo, against the [API contract](#frontend-integration-api-contract) |

## Configuration

All settings are environment variables, read from `.env`. Every setting is
listed and explained in [.env.example](.env.example). The ones you are most
likely to change:

| Setting | What it does |
|---------|--------------|
| `APP_ENV` | `local`, or `production` for a public machine. `production` makes the orchestrator refuse placeholder secrets |
| `JWT_SECRET`, `POSTGRES_PASSWORD` | Secrets. See [Secrets](#secrets) |
| `CORS_ALLOW_ORIGINS` | Browser origins allowed to call the API with cookies (login, refresh, logout). The exact front-end origin, for example `https://<app>.vercel.app` |
| `ALLOWED_HOSTS` | Host names the API answers to. On the Funnel: the `ts.net` name and `localhost` |
| `ALLOW_ANONYMOUS_OPERATOR` | `true` lets `/resolve` and `/feedback` answer without a login, as an operator |
| `LLM_MODEL` | The answer model. `qwen3:8b` by default. With less GPU memory use `qwen3:4b-instruct-2507-q4_K_M`, which scores lower |
| `RESOLVE_RATE_LIMIT_PER_IP` | Requests per minute per IP. Higher behind Vercel, where every request comes from a Vercel server |
| `TS_AUTHKEY`, `TS_HOSTNAME` | The Tailscale auth key (optional) and the machine name (default `anca-api`) |

Langfuse tracing is optional: `make up-full` starts the stack with it.

### Secrets

The secrets are `JWT_SECRET`, `POSTGRES_PASSWORD`, `TS_AUTHKEY`,
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN` and `LANGFUSE_SECRET_KEY`.
They live in `.env` on the machine. There is no secrets store yet, and none are
needed in CI. Keep them out of commits, logs and images.

Outside `APP_ENV=local`, the orchestrator refuses to start when:

- `JWT_SECRET` is the placeholder or shorter than 32 characters;
- `POSTGRES_PASSWORD` is blank or a known placeholder (`rag`, `change_in_prod`);
- `ALLOWED_HOSTS` is `*`.

A new `JWT_SECRET` logs everyone out once. To change the password of a database
that already exists, run this, then set the same value as `POSTGRES_PASSWORD`:

```bash
docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "ALTER USER <POSTGRES_USER> PASSWORD '<new>'"
```

## Documentation and ingestion

| What | Where |
|------|-------|
| The documentation that answers are drawn from | `docs/working_docs/starter-kit/docs/` (submodule, the documentation team's repo) |
| The alarm catalogue (codes, titles, descriptions) | `docs/docs-proto/starter-kit/alarms/alarms.sample.json` |
| The gold answers for the eval | `docs/docs-proto/starter-kit/alarms/reference-answers.json` |

`make ingest` checks out the submodule, applies the migrations, pulls the models,
loads the alarm catalogue, and chunks and embeds the documentation into pgvector.
Only documents that changed since the last run are embedded again.

To take in the documentation team's latest changes:

```bash
git submodule update --remote docs/working_docs   # move the submodule to their latest commit
make ingest
git add docs/working_docs && git commit -m "docs: update working_docs"   # record the new pointer
```

Run `make reingest` instead after changing the chunker or `EMBEDDING_SETUP`, or
before an eval run you want to compare with others. It embeds every document
again. An index left from an earlier build retrieves the same documents with
different chunk text, which moved `fix_solved` by a whole fix
(`eval/results/ladder/README.md`). `make seed-alarms` reloads only the alarm
catalogue. How to write alarm descriptions that retrieve well is in
[docs/alarm-description-guidelines.md](docs/alarm-description-guidelines.md).

## Database migrations

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
- **Timings:** `/resolve` and `/chat` responses carry a `Server-Timing` header
  with the time per stage, in milliseconds, for example
  `retrieve;dur=42.4, rerank;dur=436.2, generate;dur=1140.7, total;dur=1619.3`.
  Browser devtools show it under Network → Timing. Code can read it from
  `performance.getEntriesByType("resource")[i].serverTiming`. An early "not covered"
  answer, which runs no pipeline, sends none.

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

There is no sign-up endpoint. Accounts are created on the backend machine with
`make user` ([step 6](#6-create-accounts)).

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

## Deployment: HTTPS and public access

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
Only `/api/v2/*` is forwarded (`docker/tailscale-serve.json`). `/metrics`, `/docs`
and `/openapi.json` stay reachable on port 8080 of the machine only.
Nothing is published on the host for it, and the orchestrator trusts forwarded
headers only from that container.

**Once, in the Tailscale admin console:**

1. DNS: enable HTTPS certificates.
2. Access controls: allow Funnel for the tag, in the policy file:
   ```json
   "tagOwners": { "tag:anca-api": ["autogroup:admin"] },
   "nodeAttrs": [ { "target": ["tag:anca-api"], "attr": ["funnel"] } ]
   ```
3. Join the tailnet, once, in either of two ways:
   - **Login link (no key):** run `make funnel-login`. It prints a
     `login.tailscale.com` URL. Open it on any device signed in to the tailnet and
     approve the machine. If the tailnet requires device approval, also approve it
     on the Machines page.
   - **Auth key:** Settings → Keys → generate a reusable key with the tag
     `tag:anca-api`, and put the whole key in `.env` as `TS_AUTHKEY`. Copy it from
     the dialog: the key list only shows a short ID, which does not work.

   The identity is then saved in the `tailscale-state` volume, so later starts need
   neither.

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

**After a reboot.** Every service started by `make funnel` has
`restart: unless-stopped`, so the whole stack comes back by itself, with the GPU
and the Funnel, as soon as Docker Desktop is running. Docker Desktop is a desktop
app: it starts when the Windows user signs in (Docker Desktop → Settings →
General → "Start Docker Desktop when you sign in"). If the machine sits at the
Windows sign-in screen, nothing runs until someone signs in. To check or recover
by hand, run `make funnel` in WSL. It only recreates what changed, then runs the
checks. `make funnel-off` stops the Funnel, and the restart policy does not bring
it back while it is stopped.

In this setup Ollama keeps the models loaded (`OLLAMA_KEEP_ALIVE=-1`), so an idle
gap does not slow the next answer. A warm answer takes about 1 s. The first answer
after the orchestrator or Ollama restarts can take up to about 2 minutes, while the
models load from disk.

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
- Open the app once after any restart and before a demo, so the first slow
  answer is not a user's. The machine must stay on, with Docker Desktop
  running.

## Evaluation

`make eval` scores the running engine against the gold answers: whether it cites
the right documents, and whether its steps contain the fix. `EVAL_RUNS=10 make eval`
runs every alarm 10 times, to show the variation between runs. Results, including
each alarm's generated steps, go to `eval/results/retrieval.json`. That file is
committed only for a result worth recording. Normally leave it uncommitted.

- What each score means: [eval/README.md](eval/README.md).
- The current scores, what has been tried, and the open gaps:
  [docs/answer-quality.md](docs/answer-quality.md).

## Development

```bash
make fmt         # format and auto-fix with ruff
make lint        # ruff + pylint (report only)
make test        # unit tests
make retest      # unit tests -> restart the orchestrator -> bench -> eval
```

**CI:** `.github/workflows/ci.yml` runs on every push and PR on hosted runners:
ruff, pylint, mypy, pytest and an image build. It never loads a model.
Model-backed code sits behind `Protocol` interfaces and is faked in the tests,
which keeps CI free of GPUs. `eval.yml` is disabled until a self-hosted GPU
runner exists.

**Fresh WSL machine without Docker Desktop:** `make bootstrap` installs Docker
Engine and the NVIDIA Container Toolkit if they are missing, then runs the setup
steps through to `make smoke`. With Docker Desktop, follow
[Set up a new instance](#set-up-a-new-instance) instead.
