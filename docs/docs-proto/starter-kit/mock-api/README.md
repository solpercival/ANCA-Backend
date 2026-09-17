# ANCA Mate — mock API

A tiny, **offline** stand-in for the real retrieval engine. It implements the
[interface contract](./INTERFACE.md) ([`openapi.yaml`](./openapi.yaml)) and returns the curated
answers in [`../alarms/reference-answers.json`](../alarms/reference-answers.json). No AI, no internet,
no API keys — so every team can build against a stable target from day one and swap in a real
engine (or their own) later, because it honours the same shapes.

## Run it

```bash
cd mock-api
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Then open the interactive docs: **http://localhost:8000/docs**

## Endpoints

| Method & path | What it does |
|---|---|
| `POST /api/v1/resolve` | Resolve an alarm into operator guidance. Honours the `X-ANCA-Tier` header. |
| `GET  /api/v1/alarms` | List the sample alarm catalogue (handy for demos / generating QR codes). |
| `GET  /api/v1/search?q=…` | Naive keyword search over the alarm knowledge. |

## Try it

```bash
# Operator tier — concise answer, no AI chat
curl -X POST localhost:8000/api/v1/resolve \
  -H 'Content-Type: application/json' -H 'X-ANCA-Tier: operator' \
  -d '{"code":"16-0002","env":{"versions":{"core":"1.11.0"},"locale":"en-US"}}'

# Technician tier — adds likely_causes, ai_chat_available: true
curl -X POST localhost:8000/api/v1/resolve \
  -H 'Content-Type: application/json' -H 'X-ANCA-Tier: technician' \
  -d '{"code":"10-0003","env":{"versions":{"core":"1.11.0","oem":"3.2.1"},"locale":"en-US"}}'

curl localhost:8000/api/v1/alarms
curl "localhost:8000/api/v1/search?q=logical%20machine"
```

## What the mock does and doesn't do

- **Does:** look up the alarm by `code`, return the reference answer, trim/expand by tier
  (`operator` = summary + steps + citations, no chat; `technician`/`partner` = + `likely_causes`,
  chat enabled), and set a `confidence` (0.9 for `full` doc coverage).
- **Doesn't:** actually read the documentation or use `text`/`context`. That's the real engine's
  job — the contract carries `text` and `context` so a real implementation can retrieve on them.
  A real `/search` would index the full `docs/` corpus rather than just the alarm knowledge.
