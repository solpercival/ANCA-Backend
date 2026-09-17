# ANCA Mate — interface contract (plain English)

This is the agreement every team builds to. The **operator app** calls this API; the **retrieval engine** implements it for real; the **mock** implements it with canned answers. Because they share this shape, any of them can be swapped for another. The formal version is `openapi.yaml` (open it in Swagger Editor or the mock's `/docs` page).

## The one call that matters: `POST /api/v1/resolve`

Given an alarm, return guidance for the operator.

**Request** (what the operator app sends after scanning a QR / opening a link):

```jsonc
{
  "code": "am.fb.0002",              // REQUIRED — the stable <origin>.<module>.<sequence> code
  "env": {                           // REQUIRED — carried by every alarm
    "versions": { "core": "1.11.0", "oem": "3.2.1" },
    "os": "Windows 10 / INtime 6.4",
    "locale": "en-US",               // language the on-screen text was in
    "machine_variant": "GCX",
    "serial": "ANCA-2023-0421"
  },
  "context": { "program": "mdi1.pp", "line": 2 },   // OPTIONAL, alarm-specific (stretch)
  "text": "…localised alarm text…"                   // OPTIONAL hint, never the key
}
```

**Header:** `X-ANCA-Tier: operator | technician | partner` (optional, defaults to `operator`).

**Response:**

```jsonc
{
  "code": "am.fb.0002",
  "title": "Drive emergency (EMCY)",
  "severity": 833,
  "severity_category": "Error",
  "domain": "Fieldbus",
  "summary": "A drive raised an emergency and is stuck in an error state.",
  "steps": ["Record the error code and register…", "Reinitialise the bus or restart…"],
  "likely_causes": ["Drive-reported fault…"],      // technician / partner only
  "citations": [{ "doc": "AMCore User Guide",
                  "path": "user-guide/troubleshoot/coe-device-errors.md",
                  "section": "Emergency Error" }],
  "tier": "operator",
  "ai_chat_available": false,
  "confidence": 0.82
}
```

## Design principles (why it's shaped this way)

- **The code is the key, not the text.** `alarm_text` is localised by the machine's OS, so resolving on it is unreliable. Retrieval keys off `code`; `text` is only a hint. Codes use the convention `<origin>.<module>.<sequence>` (e.g. `am.fb.0002` = ANCA Motion · Fieldbus · #2) — currently draft v2.
- **Every alarm carries `env`.** Software versions (Core, OEM, …), OS, locale, machine variant and serial travel with each alarm so answers can be tailored (e.g. version-specific docs) and triaged.
- **Tiers control depth, not visibility.** `operator` gets a concise answer and no AI chat; `technician`/`partner` get `likely_causes`, more technical detail, and `ai_chat_available: true`. No alarm is hidden by tier.
- **QR budget is tight.** A reliable QR holds only a few hundred bytes, so v1 needs only `code` + `env`. The app is responsible for turning a scanned QR/URL into this call.
- **Severity is an integer 1–1000**, banded as Debug (1), Info (167), Warning (500), Error (833), Fatal (1000). `severity_category` names the band.

## Supporting calls

- `GET /api/v1/alarms` — the sample alarm catalogue (useful for demos and generating test QR codes).
- `GET /api/v1/search?q=…` — free-text search across the documentation/alarm knowledge.

## Stretch goals (documented, not required for v1)

- **Smart context:** the machine pre-collects data relevant to the specific alarm — e.g. the preceding part-program lines for a PP alarm, or the relevant configuration values for a config alarm — and embeds it in `context`.
- **QR streaming:** for payloads bigger than one QR can hold, stream via a changing/animated QR code.
- **Localised retrieval:** use `locale` to answer in the operator's language even though retrieval keys off the code.
