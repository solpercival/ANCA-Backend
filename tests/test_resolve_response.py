"""Shape of the resolve response: discrete steps, doc coverage, likely causes."""
import asyncio

import pytest

from rag_engine.api.schemas import ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.interfaces import Chunk
from rag_engine.retrieval.reranker import IdentityReranker
from tests.fakes import FB_0002, FakeAlarmStore

REQ = ResolveRequest(code="am.fb.0002")


class FakeReranker:
    async def rerank(self, query, chunks, top_n):
        return chunks[:top_n]


class FakeRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    async def retrieve(self, query, top_k, where=None):
        return self._chunks


class FakeGenerator:
    def __init__(self, answer):
        self._answer = answer

    async def generate(self, prompt):
        return self._answer


def _chunks(*scores):
    texts = [
        "Alarm raised on the drive. The fault is caused by a loose EtherCAT cable.",
        "Check the drive status LEDs. This occurs when the drive loses power.",
        "Reset the drive from the HMI.",
    ]
    return [
        Chunk(chunk_id=f"c{i}", text=texts[i % len(texts)], source="manual.md", score=s)
        for i, s in enumerate(scores)
    ]


def _resolve(answer="Reset the drive [1].", chunks=None, reranker=None, tier=Tier.technician):
    orch = Orchestrator(
        FakeRetriever(chunks if chunks is not None else _chunks(0.9, 0.5)),
        reranker or FakeReranker(),
        FakeGenerator(answer),
        FakeAlarmStore(),
    )
    return asyncio.run(orch.resolve(REQ, tier))


# --- steps -----------------------------------------------------------------

def test_steps_split_one_per_line():
    resp = _resolve("Check the cable [1].\n\nReset the drive [2].\nRestart the job [3].\n")

    assert resp.steps == ["Check the cable.", "Reset the drive.", "Restart the job."]


def test_steps_strip_numbering_and_bullets_the_model_adds_anyway():
    resp = _resolve("1. Check the cable.\n2) Reset the drive.\n- Restart.\n• Verify.")

    assert resp.steps == ["Check the cable.", "Reset the drive.", "Restart.", "Verify."]


def test_single_line_answer_is_one_step():
    assert _resolve("answer").steps == ["answer"]


def _prompt():
    orch = Orchestrator(FakeRetriever([]), FakeReranker(), FakeGenerator(""), FakeAlarmStore())
    return orch._build_prompt(REQ, FB_0002, _chunks(0.9), Tier.technician)


def test_prompt_asks_for_unnumbered_lines():
    prompt = _prompt()

    assert "one line per point" in prompt
    assert "no numbering" in prompt


def test_prompt_keeps_answers_short():
    # output tokens dominate latency (~16-33 tok/s on the demo GPU)
    prompt = _prompt()

    assert "at most 4 lines" in prompt
    assert "at most 20 words" in prompt
    assert "Never copy code, program examples, coordinates, tables" in prompt


def test_prompt_asks_for_grounded_guidance_not_invented_fixes():
    prompt = _prompt()

    assert "Using ONLY the context, explain the alarm" in prompt
    assert "often will NOT contain explicit fix steps" in prompt
    assert "never invent steps" in prompt
    # refusal is for irrelevant context, not for "no explicit fix"
    assert "COVERAGE: none    (the context is unrelated to this alarm)" in prompt
    assert "If the fix is not in the context" not in prompt


def test_prompt_asks_for_coverage_header_first():
    prompt = _prompt()

    for level in ("full", "partial", "none"):
        assert f"COVERAGE: {level}" in prompt
    assert "First line" in prompt


def test_prompt_includes_alarm_message():
    assert f"Alarm message: {FB_0002.alarm_text}" in _prompt()


def test_descriptive_answer_becomes_explanation_lines():
    answer = (
        "The EtherCAT master lost contact with slave 3 [1].\n"
        "The docs describe slave state transitions but give no fix for this alarm [2].\n"
    )

    assert _resolve(answer).steps == [
        "The EtherCAT master lost contact with slave 3.",
        "The docs describe slave state transitions but give no fix for this alarm.",
    ]


@pytest.mark.parametrize(
    "marker", ["[1]", "[n]", "[N]", "[1, 2]", "[2-3]", "[1,2,3]"],
)
def test_inline_citation_markers_are_stripped_from_steps(marker):
    resp = _resolve(f"COVERAGE: partial\nCheck the cable {marker}.\nReset the drive{marker}")

    assert resp.steps == ["Check the cable.", "Reset the drive"]


def test_bracketed_text_that_is_not_a_citation_is_kept():
    resp = _resolve("COVERAGE: partial\nSet [axis] to X in the [Motion] tab.")

    assert resp.steps == ["Set [axis] to X in the [Motion] tab."]


def test_prompt_has_no_citation_markers_or_numbered_context():
    prompt = _prompt()

    assert "[n]" not in prompt
    assert "[1]" not in prompt
    assert "No citation markers or brackets" in prompt


# --- doc coverage (and the confidence derived from it) -----------------------

@pytest.mark.parametrize(
    ("header", "coverage", "confidence"),
    [
        ("COVERAGE: full", "full", 0.9),
        ("COVERAGE: partial", "partial", 0.5),
        ("**Coverage:** Full", "full", 0.9),  # markdown / case the model may add
        ("coverage=partial", "partial", 0.5),
    ],
)
def test_coverage_header_is_parsed_and_stripped(header, coverage, confidence):
    resp = _resolve(f"{header}\nCheck the cable [1].\nReset the drive [2].")

    assert resp.doc_coverage == coverage
    assert resp.confidence == confidence
    assert resp.steps == ["Check the cable.", "Reset the drive."]


def test_coverage_none_with_guard_line():
    resp = _resolve("COVERAGE: none\nThe documentation does not cover this alarm.")

    assert resp.doc_coverage == "none"
    assert resp.confidence == 0.0
    assert resp.steps == ["The documentation does not cover this alarm."]


def test_grounding_guard_overrides_optimistic_header():
    resp = _resolve("COVERAGE: full\nThe documentation does not cover this alarm.")

    assert resp.doc_coverage == "none"
    assert resp.steps == ["The documentation does not cover this alarm."]


# guard is all-or-nothing: the disclaimer never sits in a list of real steps

REAL = ["Check the spline control points.", "Add a third control point before splineoff."]


@pytest.mark.parametrize("header", ["COVERAGE: partial", "COVERAGE: full", "COVERAGE: none", ""])
def test_disclaimer_after_real_steps_is_dropped_and_coverage_is_partial(header):
    # am.nc.0003/0004 on the bench: four real steps, then "step 5: not covered"
    answer = "\n".join([header, *REAL, "The documentation does not cover this alarm."])

    resp = _resolve(answer)

    assert resp.steps == REAL
    assert resp.doc_coverage == "partial"
    assert resp.confidence == 0.5


@pytest.mark.parametrize(
    "disclaimer",
    [
        "The documentation does not cover this alarm",  # no full stop
        "the documentation does NOT cover this alarm.",  # case
        "Beyond this, the documentation does not cover this alarm.",  # embedded
    ],
)
def test_disclaimer_variants_are_recognised(disclaimer):
    resp = _resolve("\n".join(["COVERAGE: partial", *REAL, disclaimer]))

    assert resp.steps == REAL

    alone = _resolve(f"COVERAGE: partial\n{disclaimer}")
    assert alone.doc_coverage == "none"
    assert alone.steps == ["The documentation does not cover this alarm."]


def test_disclaimer_first_then_steps_is_still_partial():
    resp = _resolve("\n".join(["COVERAGE: none", "The documentation does not cover this alarm.", *REAL]))

    assert resp.steps == REAL
    assert resp.doc_coverage == "partial"


def test_causes_survive_when_a_stray_disclaimer_is_dropped():
    answer = "\n".join(
        ["COVERAGE: partial", *REAL, "The documentation does not cover this alarm.", f"CAUSE: {CAUSED}"]
    )

    resp = _resolve(answer)

    assert resp.likely_causes == [CAUSED]


@pytest.mark.parametrize("header", ["COVERAGE: full", "COVERAGE: partial"])
def test_consistent_answer_keeps_its_claimed_coverage(header):
    assert _resolve("\n".join([header, *REAL])).doc_coverage == header.split()[-1]


def test_missing_header_defaults_to_partial_and_keeps_all_lines():
    resp = _resolve("The drive lost EtherCAT contact [1].")

    assert resp.doc_coverage == "partial"
    assert resp.steps == ["The drive lost EtherCAT contact."]


def test_header_only_answer_becomes_none():
    resp = _resolve("COVERAGE: full\n\n")

    assert resp.doc_coverage == "none"
    assert resp.steps == ["The documentation does not cover this alarm."]


def test_coverage_line_later_in_answer_is_not_treated_as_header():
    resp = _resolve("Check the cable [1].\nCOVERAGE: full")

    assert resp.doc_coverage == "partial"


def test_reranker_score_no_longer_leaks_into_confidence():
    # raw RRF score under IdentityReranker used to be reported as confidence
    resp = _resolve("COVERAGE: partial\nx [1].", chunks=_chunks(0.016), reranker=IdentityReranker())

    assert resp.confidence == 0.5


# --- likely causes -----------------------------------------------------------

CAUSED = "The fault is caused by a loose EtherCAT cable."  # sentence 2 of the first chunk
OCCURS = "This occurs when the drive loses power."  # sentence 2 of the second chunk


def _with_causes(*cause_lines):
    return "\n".join(["COVERAGE: partial", "The drive lost EtherCAT contact [1].", *cause_lines])


@pytest.mark.parametrize("tier", [Tier.technician, Tier.partner])
def test_verbatim_causes_are_returned_for_privileged_tiers(tier):
    resp = _resolve(_with_causes(f"CAUSE: {CAUSED} [1]", f"CAUSE: {OCCURS} [2]"), tier=tier)

    assert resp.likely_causes == [CAUSED, OCCURS]  # doc text, no [n] markers
    assert resp.steps == ["The drive lost EtherCAT contact."]  # CAUSE lines stripped


def test_no_cause_lines_means_no_causes():
    # the context states no cause, so the model adds no CAUSE lines -> []
    assert _resolve(_with_causes()).likely_causes == []


def test_paraphrased_cause_is_rejected():
    resp = _resolve(_with_causes("CAUSE: The EtherCAT cable is probably loose or damaged [1]"))

    assert resp.likely_causes == []


def test_invented_cause_is_rejected():
    resp = _resolve(_with_causes("CAUSE: The spindle bearing has overheated [1]"))

    assert resp.likely_causes == []


def test_cause_marker_is_ignored_for_matching():
    # markers are unreliable (often [n] or always [1]); the quote is checked against all context
    assert _resolve(_with_causes(f"CAUSE: {CAUSED} [n]")).likely_causes == [CAUSED]
    assert _resolve(_with_causes(f"CAUSE: {OCCURS} [1]")).likely_causes == [OCCURS]


def test_returned_text_is_the_docs_sentence_not_the_models():
    # small slips (case, quotes, markdown, missing full stop) still anchor to the real sentence
    resp = _resolve(_with_causes('CAUSE: "the fault is caused by a **loose** EtherCAT cable" [1]'))

    assert resp.likely_causes == [CAUSED]


def test_partial_quote_resolves_to_full_sentence():
    resp = _resolve(_with_causes("CAUSE: caused by a loose EtherCAT cable [1]"))

    assert resp.likely_causes == [CAUSED]


def test_cause_from_any_retrieved_chunk_is_accepted():
    resp = _resolve(_with_causes(f"CAUSE: {OCCURS}"))

    assert resp.likely_causes == [OCCURS]


def test_causes_capped_at_three_and_deduplicated():
    chunks = [
        Chunk(chunk_id=f"c{i}", text=f"Fault {i} is caused by broken wire number {i}.", source="m.md")
        for i in range(1, 6)
    ]
    lines = [f"CAUSE: Fault {i} is caused by broken wire number {i}. [{i}]" for i in (1, 1, 2, 3, 4, 5)]

    resp = _resolve(_with_causes(*lines), chunks=chunks)

    assert resp.likely_causes == [
        "Fault 1 is caused by broken wire number 1.",
        "Fault 2 is caused by broken wire number 2.",
        "Fault 3 is caused by broken wire number 3.",
    ]


def test_likely_causes_empty_for_operator_and_lines_still_stripped():
    resp = _resolve(_with_causes(f"CAUSE: {CAUSED} [1]"), tier=Tier.operator)

    assert resp.likely_causes == []
    assert resp.steps == ["The drive lost EtherCAT contact."]


# --- no raw chunk text in likely_causes ------------------------------------------

# the fragments the bench surfaced, around one real cause sentence
MESSY_CHUNK = "\n".join([
    "## OPC UA",
    "The OPC UA server refuses connections when the licence is missing.",
    "",
    "```jsonc",
    '{ "opcua": { "enabled": true },',
    '  "port": 4840 }',
    "```",
    "",
    "| Name | Key | Description |",
    "| --- | --- | --- |",
    "| Server port | `opcua.port` | The TCP port the server listens on. |",
    "",
    "1.",
    "- **Loose** `EtherCAT` cabling causes the [drive](drives.md) to fault.",
])
LICENCE = "The OPC UA server refuses connections when the licence is missing."
CABLING = "Loose EtherCAT cabling causes the drive to fault."


def _messy(*cause_lines):
    chunks = [Chunk(chunk_id="m1", text=MESSY_CHUNK, source="opcua.md", score=0.9)]
    return _resolve(_with_causes(*cause_lines), chunks=chunks)


def test_context_sentences_skip_structure():
    from rag_engine.orchestrator import _context_sentences

    assert _context_sentences(MESSY_CHUNK) == (LICENCE, CABLING)


@pytest.mark.parametrize(
    "garbage",
    [
        '```jsonc { "opcua": { "enabled": true },',
        '{ "opcua": { "enabled": true }, "port": 4840 }',
        "| Name | Key | Description |",
        "| Server port | opcua.port | The TCP port the server listens on. |",
        "1.",
        "## OPC UA",
        "OPC UA",
    ],
)
def test_quoting_structural_fragments_yields_no_cause(garbage):
    assert _messy(f"CAUSE: {garbage}").likely_causes == []


def test_heading_does_not_fuse_into_the_cause():
    # the old flatten-then-split would have produced "## OPC UA The OPC UA server ..."
    assert _messy(f"CAUSE: OPC UA {LICENCE}").likely_causes == [LICENCE]


def test_cause_comes_back_without_markdown():
    resp = _messy("CAUSE: - **Loose** `EtherCAT` cabling causes the [drive](drives.md) to fault.")

    assert resp.likely_causes == [CABLING]


def test_real_causes_still_found_in_messy_chunk():
    assert _messy(f"CAUSE: {LICENCE}", f"CAUSE: {CABLING}").likely_causes == [LICENCE, CABLING]


def test_likely_causes_empty_when_docs_do_not_cover_alarm():
    resp = _resolve(f"COVERAGE: none\nThe documentation does not cover this alarm.\nCAUSE: {CAUSED} [1]")

    assert resp.likely_causes == []


def test_prompt_asks_privileged_tiers_for_verbatim_causes_only():
    orch = Orchestrator(FakeRetriever([]), FakeReranker(), FakeGenerator(""), FakeAlarmStore())

    tech = orch._build_prompt(REQ, FB_0002, _chunks(0.9), Tier.technician)
    oper = orch._build_prompt(REQ, FB_0002, _chunks(0.9), Tier.operator)

    assert "CAUSE: <the first 8 to 10 words of one context sentence, copied exactly>\n" in tech
    assert "Never write a cause in your own words" in tech
    assert "CAUSE:" not in oper


def test_cause_given_as_opening_words_returns_the_full_sentence():
    # the model only emits the sentence's first words; the server returns the whole of it
    resp = _resolve(_with_causes("CAUSE: The fault is caused by a loose"))

    assert resp.likely_causes == [CAUSED]


def test_opening_words_of_real_doc_sentence_resolve_to_it():
    text = (
        "### Device Unexpected State\n"
        "**Severity:** Error\n\n"
        "A device will raise a device unexpected state error when its operational "
        "state no longer matches that of the Master. **Resolution:** In the case that "
        "it is an error, reinitialise the Ethercat bus."
    )
    chunks = [Chunk(chunk_id="d1", text=text, source="coe-device-errors.md", score=0.9)]

    resp = _resolve(
        _with_causes("CAUSE: A device will raise a device unexpected state error..."),
        chunks=chunks,
    )

    assert resp.likely_causes == [
        "A device will raise a device unexpected state error when its operational "
        "state no longer matches that of the Master."
    ]


def test_too_short_an_opening_is_not_enough_to_locate_a_sentence():
    # under the 30-char partial-quote floor, a fragment could match many sentences
    assert _resolve(_with_causes("CAUSE: The fault is")).likely_causes == []


# --- through the API ---------------------------------------------------------

def _auth(tier):
    token, _ = create_access_token(user_id=1, tier=tier)
    return {"Authorization": f"Bearer {token}"}


def test_api_technician_gets_causes_and_coverage(client):
    r = client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=_auth(Tier.technician))

    assert r.status_code == 200
    body = r.json()
    assert body["likely_causes"]
    assert body["doc_coverage"] in ("full", "partial", "none")
    assert 0.0 <= body["confidence"] <= 1.0


def test_api_operator_gets_no_causes(client):
    r = client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=_auth(Tier.operator))

    assert r.status_code == 200
    assert r.json()["likely_causes"] == []
