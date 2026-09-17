# ANCA Mate — Starter Kit
### COMP30022 IT Project · Semester 2, 2026 · Client: ANCA Motion

Welcome! This kit gives your team everything you need to start building from week one — sample data, a working mock engine, and the documentation your assistant will draw on. You should never be blocked waiting on another team.

## What is ANCA Mate?

When a CNC grinding machine raises an **alarm**, the operator has to work out what it means and how to fix it — usually by hunting through dense technical docs while production waits. **ANCA Mate** is a browser-based assistant that shortcuts this: the operator scans a **QR code** at the machine, the alarm loads into a mobile-friendly web app, and AI retrieves the right guidance from the documentation and presents clear, step-by-step help.

## How the workshop is organised

Six teams, working across **three project streams — two teams per stream**. The two teams on a stream are friendly rivals; the strongest ideas converge later in the semester.

1. **Retrieval engine** — the "brain". A Retrieval-Augmented Generation (RAG) pipeline that, given an alarm, finds the most relevant material in the docs and produces a grounded answer with citations. Works directly off the **Markdown** source (not the built PDFs).
2. **Documentation & alarm pipeline** — the "supply chain". How Markdown docs get published and versioned into a form the engine can ingest, and how a machine **alarm should best be documented** (a real, unsolved problem at ANCA).
3. **Operator assistant** — the "face". The end-to-end experience the operator uses: scan a QR → the alarm loads on a phone → clear guidance appears. Differentiate on conversational troubleshooting, tiered access, factory-floor UX, or a feedback loop.

Everyone builds against the same **starter kit** below, so no stream waits on another. Every team can run the mock engine from day one and swap in the real one at integration.

## What's in this kit

```
starter-kit/
├── README.md                     ← you are here
├── NOTICE.md                     ← usage & confidentiality (please read)
├── docs/                         ← the documentation corpus (Markdown)
│   ├── user-guide/               ← AMCore User Guide
│   └── part-programmers-reference/  ← Part Programmer's Reference
├── alarms/
│   ├── alarms.sample.json        ← sample alarm INPUTS (what the machine emits / a QR carries)
│   └── reference-answers.json    ← curated "gold" answers (ground truth + what the mock serves)
├── brand/                        ← logo + brand basics for the operator-assistant teams
│   ├── anca-motion-logo-colour.png
│   ├── anca-motion-logo-white.png
│   └── BRAND.md
└── mock-api/
    ├── app.py                    ← the offline mock engine (FastAPI)
    ├── requirements.txt
    ├── openapi.yaml              ← the interface contract (formal)
    ├── INTERFACE.md              ← the interface contract (plain English)
    └── README.md                 ← how to run the mock
```

## How the pieces fit together

```
[machine alarm] --QR / URL--> [Operator assistant] --POST /resolve--> [Engine: mock, then real]
                                                                             ^
                                            [Docs & alarm pipeline] feeds --> [ docs/ corpus ]
```

- The **alarm** (its `code` + environment) is what a QR code carries. The **operator assistant** turns a scan into a `POST /api/v1/resolve` call.
- The **engine** answers that call. Use the **mock** now; drop in the real engine later — same contract.
- The **pipeline** keeps the `docs/` corpus in a shape the engine can consume.

## Get started in five minutes

```bash
cd mock-api
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000/docs** for an interactive page you can click through, then read [`mock-api/INTERFACE.md`](./mock-api/INTERFACE.md) for the contract in plain English.

## Key things to know

- **The alarm `code` (e.g. `am.fb.0002`) is the stable key.** The on-screen `alarm_text` is localised by the machine's OS, so it's only a hint — resolve on the code. Codes follow the convention `<origin>.<module>.<sequence>` — origin `am` = ANCA Motion core platform, module = a short architecture token (`fb` Fieldbus, `nc` Numerical Controller, `cfg` Configuration, `lic` Licensing, …). This convention is currently **draft v2** and may still be refined.
- **Every alarm carries an `env` block** (software versions, OS, locale, machine variant, serial). Use it to tailor answers and for triage.
- **Access is by tier** (`X-ANCA-Tier: operator | technician | partner`): higher tiers get more technical detail and AI chat. It changes depth, not which alarms you can see.
- **`reference-answers.json` is your ground truth.** Use it to measure how well your assistant retrieves and answers. Each answer has a `doc_coverage` flag (`full` where the docs contain the fix).
- **The docs are real and work-in-progress.** Some pages are marked DRAFT and there are known issues (see `_known_doc_issues` in `reference-answers.json` — e.g. some log-file paths are believed incorrect). That's realistic; part of the challenge is dealing with imperfect source material.
- **Everything here runs on free / open-source tooling.** You don't need any ANCA infrastructure, paid services, or API keys.
- **Please keep these materials private** — use private repos and don't publish the ANCA-provided content. See [`NOTICE.md`](./NOTICE.md).
- **A light brand kit is in [`brand/`](./brand/BRAND.md)** (logo + colours + fonts) so the operator-assistant app can look on-brand.

## Stretch goals (not required — but where the interesting problems are)

- **Smart context:** have the machine pre-collect data relevant to the specific alarm — e.g. the preceding part-program lines for a PP alarm, or the relevant configuration values for a config alarm — and embed it in the QR.
- **QR streaming:** stream a payload bigger than one QR can hold via a changing/animated QR code.
- **Localised answers:** use `env.locale` to answer in the operator's language even though retrieval keys off the code.
- **Tiered access & auth:** turn the tier header into real authentication with capability tiers.
- **Feedback loop:** capture whether a resolution helped, and surface common alarms and gaps in the docs.

## A note on the sample data

The sample alarm codes use a **draft** identifier convention — `<origin>.<module>.<sequence>` (e.g. `am.fb.0002`) — that ANCA Motion is considering for future use. Today there is no single consistent alarm-ID convention across the production systems, so treat this as a proposal, not established practice. The specific codes and some wording are illustrative — a representative starting set, not a definitive alarm list.

## Questions?

Your ANCA Motion client contact is **Tim Comport** (Manager, Software & AI). Bring questions to the client sessions — the harder ones (like how alarms *should* be documented) are exactly what we're hoping you'll help us figure out.
