"""
ANCA Mate — mock API.

A tiny, offline stand-in for the real retrieval engine. It implements the
interface contract (see openapi.yaml / INTERFACE.md) and returns curated
reference answers so the operator-app and other teams can build from day one.
No AI, no internet, no keys — it just serves alarms.sample.json +
reference-answers.json.

Run:
    pip install -r requirements.txt
    uvicorn app:app --reload --port 8000
Then open http://localhost:8000/docs
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
ALARMS_DIR = BASE.parent / "alarms"

_alarms_doc = json.loads((ALARMS_DIR / "alarms.sample.json").read_text(encoding="utf-8"))
_answers_doc = json.loads((ALARMS_DIR / "reference-answers.json").read_text(encoding="utf-8"))

ALARMS: List[dict] = _alarms_doc["alarms"]
ALARM_BY_CODE: Dict[str, dict] = {a["code"]: a for a in ALARMS}
ANSWERS: Dict[str, dict] = _answers_doc["answers"]

VALID_TIERS = ("operator", "technician", "partner")

app = FastAPI(
    title="ANCA Mate API (mock)",
    version="1.0.0",
    description=(
        "Offline mock of the ANCA Mate alarm-resolution assistant. Serves curated "
        "reference answers per the interface contract. Swap it for a real engine that "
        "honours the same shapes. See INTERFACE.md and openapi.yaml."
    ),
)


# ---- models (mirror openapi.yaml) ----
class Env(BaseModel):
    versions: Dict[str, str] = Field(..., example={"core": "1.11.0", "oem": "3.2.1"})
    locale: str = Field(..., example="en-US")
    os: Optional[str] = Field(None, example="Windows 10 / INtime 6.4")
    machine_variant: Optional[str] = Field(None, example="GCX")
    serial: Optional[str] = Field(None, example="ANCA-2023-0421")


class ResolveRequest(BaseModel):
    code: str = Field(..., example="16-0002")
    env: Env
    context: Optional[Dict[str, Any]] = None
    text: Optional[str] = None


def _normalise_tier(raw: Optional[str]) -> str:
    tier = (raw or "operator").strip().lower()
    return tier if tier in VALID_TIERS else "operator"


@app.post("/api/v1/resolve")
def resolve(
    req: ResolveRequest,
    x_anca_tier: Optional[str] = Header(default="operator", alias="X-ANCA-Tier"),
):
    """Resolve an alarm into operator guidance. Depth/chat depend on the tier."""
    tier = _normalise_tier(x_anca_tier)
    alarm = ALARM_BY_CODE.get(req.code)
    answer = ANSWERS.get(req.code)
    if alarm is None or answer is None:
        raise HTTPException(status_code=404, detail=f"Unknown alarm code: {req.code}")

    resp: Dict[str, Any] = {
        "code": req.code,
        "title": alarm["title"],
        "severity": alarm["severity"],
        "severity_category": alarm["severity_category"],
        "domain": alarm["domain"],
        "summary": answer["summary"],
        "steps": answer["resolution_steps"],
        "citations": answer["doc_refs"],
        "tier": tier,
        "ai_chat_available": tier != "operator",
        "confidence": 0.9 if answer.get("doc_coverage") == "full" else 0.5,
    }
    # Higher tiers get the extra technical detail.
    if tier in ("technician", "partner"):
        resp["likely_causes"] = answer.get("likely_causes", [])
    return resp


@app.get("/api/v1/alarms")
def list_alarms():
    """The sample alarm catalogue (useful for demos and generating test QR codes)."""
    keys = ("code", "title", "domain", "severity", "severity_category", "alarm_text")
    return [{k: a.get(k) for k in keys} for a in ALARMS]


@app.get("/api/v1/search")
def search(q: str = Query(..., min_length=1)):
    """Naive offline search over the alarm knowledge. A real engine searches the full docs."""
    terms = [t for t in re.findall(r"\w+", q.lower()) if len(t) > 1]
    results = []
    for a in ALARMS:
        ans = ANSWERS.get(a["code"], {})
        haystack = " ".join(
            [a["title"], a["alarm_text"], ans.get("summary", ""), " ".join(ans.get("resolution_steps", []))]
        ).lower()
        score = sum(haystack.count(t) for t in terms)
        if score > 0:
            cite = (ans.get("doc_refs") or [None])[0]
            results.append(
                {
                    "score": float(score),
                    "title": a["title"],
                    "snippet": ans.get("summary") or a["alarm_text"][:200],
                    "citation": cite,
                }
            )
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:10]


@app.get("/")
def root():
    return {"service": "ANCA Mate mock API", "docs": "/docs", "alarms": len(ALARMS)}
