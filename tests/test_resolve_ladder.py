"""The resolve experiment switches (RESOLVE_PROMPT, RESOLVE_EVIDENCE_FIRST,
RESOLVE_SENTENCE_SELECT) and the gap diagnosis that measures them. All are off by
default; these pin what each one does when switched on."""

import asyncio

from eval.diagnose_gaps import diagnose
from rag_engine.api.schemas import ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.config import get_settings
from rag_engine.orchestrator import Orchestrator, _context_units
from rag_engine.retrieval.interfaces import Chunk
from tests.fakes import FB_0002, FakeAlarmStore, FakePreprocessor

CONTEXT = (
    "The drive reports an emergency when it detects a fault. "
    "In the case that it is an error, recover by reinitialising the Ethercat bus.\n"
    "Restarting the system also clears the error state of the drive."
)


class Retriever:
    async def retrieve(self, query, top_k, where=None):
        return [Chunk(chunk_id="c1", text=CONTEXT, source="coe.md", score=0.9)]


class Reranker:
    async def rerank(self, query, chunks, effort):
        return chunks


class Generator:
    def __init__(self, answer):
        self.answer = answer
        self.prompt = ""

    async def generate(self, prompt, tokens=None, thinking=False):
        self.prompt = prompt
        return self.answer


def _resolve(answer):
    generator = Generator(answer)
    orch = Orchestrator(FakePreprocessor(), Retriever(), Reranker(), generator, FakeAlarmStore())
    resp = asyncio.run(orch.resolve(ResolveRequest(code=FB_0002.code), Tier.technician))
    return resp, generator.prompt


def test_short_prompt_has_five_rules_and_the_context_right_before_the_question(monkeypatch):
    monkeypatch.setattr(get_settings(), "resolve_prompt", "short")

    _, prompt = _resolve("COVERAGE: full\nReinitialise the Ethercat bus")

    rules = [ln for ln in prompt.splitlines() if ln[:2] in {"1.", "2.", "3.", "4.", "5."}]
    assert len(rules) == 5
    tail = prompt.rsplit("Context:\n", 1)[1]
    assert tail.index("Question:") > tail.index("reinitialising the Ethercat bus")
    assert "printer" in prompt  # the examples are from another domain


def test_evidence_first_keeps_backed_steps_in_context_order(monkeypatch):
    monkeypatch.setattr(get_settings(), "resolve_evidence_first", True)

    resp, prompt = _resolve(
        "COVERAGE: full\n"
        "EVIDENCE: In the case that it is an error, recover by\n"
        "EVIDENCE: Restarting the system also clears the error state\n"
        "Restart the system to clear the error\n"
        "Replace the hydraulic pump filter\n"
        "Reinitialise the Ethercat bus to recover the drive\n"
    )

    assert "EVIDENCE:" in prompt
    # the unbacked step is dropped; the rest follow their evidence's order
    assert resp.steps == [
        "Reinitialise the Ethercat bus to recover the drive",
        "Restart the system to clear the error",
    ]


def test_context_units_keep_table_rows_under_their_header():
    text = "Intro sentence one. Sentence two.\n\n| Name | Meaning |\n| --- | --- |\n| E1 | Fault |\n"

    assert _context_units(text) == [
        "Intro sentence one.",
        "Sentence two.",
        "| Name | Meaning |\n| E1 | Fault |",
    ]


def test_gap_is_in_prompt_when_the_context_holds_the_gold_step():
    gold = {"am.fb.0002": {"resolution_steps": ["Reinitialise the EtherCAT bus to recover."]}}
    results = [{"code": "am.fb.0002", "steps": ["Check the drive status LEDs."]}]

    in_prompt = diagnose(results, gold, {"am.fb.0002": CONTEXT})
    absent = diagnose(results, gold, {"am.fb.0002": "Unrelated text about spindles."})

    assert in_prompt["am.fb.0002"][0]["status"] == "in_prompt_not_used"
    assert absent["am.fb.0002"][0]["status"] == "not_in_prompt"
