"""Shape of the resolve response: discrete steps, doc coverage, likely causes."""

import asyncio

import pytest

from rag_engine.api.schemas import ResolveRequest
from rag_engine.auth.tiers import Tier
from rag_engine.auth.tokens import create_access_token
from rag_engine.config import API_PREFIX, get_settings
from rag_engine.orchestrator import Orchestrator
from rag_engine.retrieval.interfaces import Alarm, Chunk
from rag_engine.retrieval.reranker import IdentityReranker
from tests.fakes import FB_0002, FakeAlarmStore, FakePreprocessor

REQ = ResolveRequest(code="am.fb.0002")


class FakeReranker:
    async def rerank(self, query, chunks, effort):
        return chunks[: effort.reranker_n]


class FakeRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    async def retrieve(self, query, top_k, where=None):
        return self._chunks


class FakeGenerator:
    def __init__(self, answer):
        self._answer = answer

    async def generate(self, prompt, tokens=None, thinking=False):
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
        FakePreprocessor(),
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
    orch = Orchestrator(
        FakePreprocessor(), FakeRetriever([]), FakeReranker(), FakeGenerator(""), FakeAlarmStore()
    )
    return orch._build_prompt(REQ, FB_0002, _chunks(0.9), Tier.technician)


def test_prompt_asks_for_unnumbered_lines():
    prompt = _prompt()

    assert "one line per point" in prompt
    assert "no numbering" in prompt


def test_prompt_keeps_answers_short():
    # output tokens dominate latency (~16-33 tok/s on the demo GPU)
    prompt = _prompt()

    assert "at most 20 words" in prompt
    assert "Never copy code, program examples, coordinates, tables" in prompt


def test_prompt_lets_the_docs_set_the_number_of_steps():
    # a fixed shape padded am.lic.0001 (one fix, three times) and truncated am.fb.0002
    prompt = _prompt()

    assert "as many or as few steps as the context supports" in prompt
    assert "no fixed number and no minimum" in prompt
    assert "Never repeat a step in different words" in prompt
    # bench: with no count, padding came back as Check/Verify lines instead
    # (am.lic.0001: check, verify, set, ensure, restart; am.nc.0004 restated its rule)
    assert "Add a Check or Verify step only when" in prompt
    assert "checks whether another step was done" in prompt
    assert "restates a step or a rule as a check" in prompt
    assert "Make sure no step would cause this alarm" in prompt
    # v3's strength kept without its count: the fix first, as an action
    assert "Put first the step that resolves the alarm" in prompt
    assert "not as a check that it was done" in prompt
    # the gold answers branch ("If PLC: ...", "If you do need it, contact ANCA ...")
    assert "start with that condition instead, then the verb" in prompt
    # bench: a concrete example sentence here was copied verbatim into am.fb.0001
    assert '"If <condition from the context>, <verb> ..."' in prompt
    assert "If the error code is non-zero" not in prompt
    assert "Give each alternative the context offers as its own conditional step" in prompt
    assert "at most 4 lines" not in prompt
    assert "at most two diagnostic lines" not in prompt


def test_prompt_forbids_example_specific_values():
    prompt = _prompt()

    assert "Never reproduce example-specific identifiers or values" in prompt
    for example in ("Drive_3", "0x03", "devices 2, 4 and 5", "coordinates"):
        assert example in prompt
    assert "Check the drive's reported error register" in prompt
    # config properties and documented rules are not examples
    assert "Configuration property names" in prompt
    assert "limits it states as rules are not examples" in prompt


def test_prompt_asks_for_grounded_guidance_not_invented_fixes():
    prompt = _prompt()

    assert "Using ONLY the context, tell the technician how to resolve this alarm" in prompt
    assert "often will NOT contain explicit fix steps" in prompt
    assert "never invent steps" in prompt
    # refusal is for irrelevant context, not for "no explicit fix"
    assert "COVERAGE: none    (the context is unrelated to this alarm)" in prompt
    assert "If the fix is not in the context" not in prompt


def test_prompt_asks_for_actionable_steps_not_restatements():
    # bench showed steps restating the alarm and leaking off-topic chunks
    prompt = _prompt()

    assert "Start each line with a verb" in prompt
    assert "short imperative sentence" in prompt
    # bench: the restart fix was missing when the docs said it was required
    assert "requires a restart or reinitialisation, that must be one of the lines" in prompt
    assert "Never write a line that only describes the alarm" in prompt
    assert "Fewer lines are better than filler" in prompt
    assert "Ignore context about a different task or feature" in prompt


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
    "marker",
    ["[1]", "[n]", "[N]", "[1, 2]", "[2-3]", "[1,2,3]"],
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
    resp = _resolve(
        "\n".join(["COVERAGE: none", "The documentation does not cover this alarm.", *REAL])
    )

    assert resp.steps == REAL
    assert resp.doc_coverage == "partial"


def test_causes_survive_when_a_stray_disclaimer_is_dropped():
    answer = "\n".join(
        [
            "COVERAGE: partial",
            *REAL,
            "The documentation does not cover this alarm.",
            f"CAUSE: {CAUSED}",
        ]
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


def test_non_action_filler_beside_action_steps_is_dropped():
    # real eval output: a doc-example line slipped in after the actual fix
    resp = _resolve(
        "COVERAGE: partial\n"
        "Set the Joint logical device for the joint to the logical address of the device.\n"
        "Verify the logical device is assigned to only one joint.\n"
        "Data-block mapping maps device 1 to devices 2, 4, and 5.\n"
    )

    assert resp.steps == [
        "Set the Joint logical device for the joint to the logical address of the device.",
        "Verify the logical device is assigned to only one joint.",
    ]


def test_explanation_only_answer_is_kept_whole():
    # no action line at all: the docs explain but give no fix, which is legitimate
    answer = (
        "COVERAGE: partial\nThe drive lost EtherCAT contact [1].\nThe master resets the bus [2]."
    )

    assert _resolve(answer).steps == [
        "The drive lost EtherCAT contact.",
        "The master resets the bus.",
    ]


def test_disclaimer_is_not_treated_as_filler():
    # _settle_coverage, not the filler filter, decides what happens to the disclaimer
    resp = _resolve(
        "\n".join(["COVERAGE: full", *REAL, "The documentation does not cover this alarm."])
    )

    assert resp.steps == REAL
    assert resp.doc_coverage == "partial"


def test_step_the_context_does_not_back_up_is_dropped(monkeypatch):
    # a reworded doc step stays; one with no basis in the context is invented
    monkeypatch.setattr(get_settings(), "step_support_min", 0.5)

    resp = _resolve(
        "COVERAGE: partial\n"
        "Reset the drive using the HMI.\n"
        "Replace the hydraulic pump filter cartridge.\n",
        chunks=_chunks(0.9, 0.5, 0.4),
    )

    assert resp.steps == ["Reset the drive using the HMI."]


def test_resolve_turn_is_recorded_under_the_callers_conversation():
    recorded = []

    class RecordingPreprocessor(FakePreprocessor):
        def store_context(self, conversation_id, query, response, alarm):
            recorded.append((conversation_id, response, alarm))

    orch = Orchestrator(
        RecordingPreprocessor(),
        FakeRetriever(_chunks(0.9, 0.5)),
        FakeReranker(),
        FakeGenerator("Check the cable [1].\nReset the drive [2]."),
        FakeAlarmStore(),
    )
    req = ResolveRequest(code="am.fb.0002", conversation_id="c-1")

    asyncio.run(orch.resolve(req, Tier.technician))

    # the steps as returned, not the raw model output
    assert recorded == [("c-1", "Check the cable.\nReset the drive.", "am.fb.0002")]


# --- step count follows the docs; repeats collapse ---------------------------


def test_repeated_instruction_collapses_to_one_step():
    # am.lic.0001 on the bench: the single documented fix, restated three times
    resp = _resolve(
        "COVERAGE: full\n"
        "Set opcua.enable to false.\n"
        "Set the configuration property opcua.enable to false.\n"
        "Set opcua.enable = false in the configuration.\n"
    )

    assert resp.steps == ["Set opcua.enable to false."]
    assert resp.doc_coverage == "full"


def test_fix_restated_as_checks_collapses_to_the_fix():
    # v3 bench, am.lic.0001: the fix, then the same fix twice more as checks
    resp = _resolve(
        "COVERAGE: full\n"
        "Disable opcua.server with opcua.enable set to false\n"
        "Verify opcua.enable is set to false in configuration\n"
        "Check opcua.enable property is false in configuration file\n"
    )

    assert resp.steps == ["Disable opcua.server with opcua.enable set to false"]


@pytest.mark.parametrize(
    "steps",
    [
        # a check with its own object is a real diagnostic, not a restatement
        [
            "Set the Joint logical device for the joint to the logical address of the device.",
            "Verify the logical device is assigned to only one joint.",
        ],
        # v3 bench, am.nc.0004: the check adds where the points go
        [
            "Add at least three control points between splineon and splineoff.",
            "Verify points are specified after splineon and before splineoff.",
            "Check that fm and st are only on the splineon block.",
        ],
        # only checks are judged against earlier steps: two actions are kept
        ["Enable the drive watchdog timer.", "Disable the drive watchdog timer."],
        # the check states a different value than the action
        ["Set opcua.enable to false.", "Verify opcua.enable is true after the restart."],
    ],
)
def test_checks_that_add_something_are_kept(steps):
    assert _resolve("\n".join(["COVERAGE: partial", *steps])).steps == steps


def test_exact_repeat_differing_only_in_case_and_punctuation_collapses():
    resp = _resolve("COVERAGE: partial\nRestart AMCore.\nrestart AMCore\nCheck the cable.")

    assert resp.steps == ["Restart AMCore.", "Check the cable."]


@pytest.mark.parametrize(
    "steps",
    [
        ["Check the drive's error register.", "Check the drive's status register."],
        ["Check the cable.", "Check the cable connector."],  # too short to judge: kept
        REAL,
    ],
)
def test_similar_but_distinct_steps_are_kept(steps):
    assert _resolve("\n".join(["COVERAGE: partial", *steps])).steps == steps


def test_long_documented_procedure_is_not_truncated():
    # am.fb.0002: the zero/non-zero error code check was cut by the old 3-line shape
    steps = [
        "Check the drive's reported error code.",
        "Interpret a zero error code as a communication loss, not a drive fault.",
        "Inspect the EtherCAT cable for a non-zero error code.",
        "Reset the drive from the HMI.",
        "Restart the job once the drive reports OP state.",
    ]

    assert _resolve("\n".join(["COVERAGE: full", *steps])).steps == steps


def test_single_documented_step_is_not_padded():
    assert _resolve("COVERAGE: full\nSet opcua.enable to false.").steps == [
        "Set opcua.enable to false."
    ]


# --- example-specific literals from the docs ---------------------------------


@pytest.mark.parametrize(
    "step",
    [
        "Verify the error register is 0x04.",
        "Reset Drive_3 at station 0x03.",
        "Check the data-block mapping of devices 2, 4 and 5.",
        "Check stations 1 and 3 for a cable fault.",
        'Restart the drive named "Drive 3".',
    ],
)
def test_step_stating_an_example_value_as_fact_is_dropped(step):
    resp = _resolve(f"COVERAGE: partial\nReset the drive from the HMI.\n{step}")

    assert resp.steps == ["Reset the drive from the HMI."]


@pytest.mark.parametrize(
    ("step", "generalised"),
    [
        (
            "Check the drive's reported error register (e.g. 0x04).",
            "Check the drive's reported error register.",
        ),
        (
            "Check the error register, for example 0x04.",
            "Check the error register.",
        ),
        (
            "Check which device is in SAFEOP (such as Drive_3) in the log.",
            "Check which device is in SAFEOP in the log.",
        ),
    ],
)
def test_example_value_in_an_aside_is_cut_and_the_step_kept(step, generalised):
    assert _resolve(f"COVERAGE: partial\n{step}").steps == [generalised]


@pytest.mark.parametrize(
    "step",
    [
        "Set opcua.enable to false.",
        "Set mcode.101.mode = 5 to handle M101 in PLC.",
        "Ensure there are at least 3 control points between splineon and splineoff.",
        "Check whether the drive's error code is zero or non-zero.",
        "Configure the M-code to a PLC mode (1-3 or 5-7).",
        "Set the axis in the [Motion] tab, such as the spindle axis.",
        "Check that slave 3 responds.",
    ],
)
def test_documented_values_and_rules_are_not_scrubbed(step):
    assert _resolve(f"COVERAGE: full\n{step}").steps == [step]


def test_coe_object_addresses_are_not_scrubbed_but_values_are():
    # gold am.fb.0002: 0x1001:00 / 0x1004:00 are fixed CoE objects, not one machine's
    record = "Record the error code (0x1001:00) and error register (0x1004:00)."
    resp = _resolve(f"COVERAGE: full\n{record}\nCheck the error register 0x04: overcurrent.")

    assert resp.steps == [record]


FB_0004 = Alarm(
    code="am.fb.0004",
    title="Device firmware mismatch",
    domain="Fieldbus",
    severity_score=833,
    severity_category="error",
    alarm_text="Fieldbus: device 'Drive_3' is running firmware 1.2.0 but 1.4.0 is expected.",
    data_fields={},
)


def _resolve_alarm(alarm, answer, chunks=None):
    orch = Orchestrator(
        FakePreprocessor(),
        FakeRetriever(chunks if chunks is not None else _chunks(0.9, 0.5)),
        FakeReranker(),
        FakeGenerator(answer),
        FakeAlarmStore(alarm),
    )
    return asyncio.run(orch.resolve(ResolveRequest(code=alarm.code), Tier.technician))


def test_value_from_the_alarm_message_is_not_a_doc_example():
    """The alarm names the caller's own device; a step naming it is not repeating a
    doc example (bench: every am.fb.0004 step was dropped for saying Drive_3)."""
    steps = [
        "Run the device-firmware-upload.exe --auto command to update Drive_3 firmware.",
        "Check that Drive_3 reports firmware version 1.4.0 after the upload completes.",
    ]

    resp = _resolve_alarm(FB_0004, "\n".join(["COVERAGE: full", *steps]))

    assert resp.steps == steps
    assert resp.doc_coverage == "full"


def test_other_example_values_are_still_dropped_for_that_alarm():
    resp = _resolve_alarm(
        FB_0004,
        "COVERAGE: full\nUpload the firmware to Drive_3.\nReset Drive_7 at station 0x03.",
    )

    assert resp.steps == ["Upload the firmware to Drive_3."]


def test_hex_value_from_the_alarm_message_is_still_scrubbed():
    """Only device names get the pass. A step repeating the alarm's hex value goes on
    to say what it means, which the docs don't state (bench, am.fb.0002)."""
    emcy = Alarm(
        code="am.fb.0002",
        title="Drive emergency (EMCY)",
        domain="Fieldbus",
        severity_score=833,
        severity_category="error",
        alarm_text=(
            "Fieldbus: emergency reported by drive 'Drive_3' — error code 0x2350, "
            "error register 0x04."
        ),
        data_fields={},
    )

    resp = _resolve_alarm(
        emcy,
        "COVERAGE: partial\n"
        "Reinitialise the EtherCAT bus.\n"
        "If the error register shows 0x04, check for frame response errors.\n"
        'Restart "Drive_3" if the emergency returns.',
    )

    assert resp.steps == [
        "Reinitialise the EtherCAT bus.",
        'Restart "Drive_3" if the emergency returns.',
    ]


def test_medium_effort_reranks_thirty_candidates():
    """The embedding search ranked the right section 25th for am.cfg.0001; with only
    the first 10 passed on, the reranker never saw it."""
    seen = []

    class RecordingReranker:
        async def rerank(self, query, chunks, effort):
            seen.append(len(chunks))
            return chunks[: effort.reranker_n]

    orch = Orchestrator(
        FakePreprocessor(),
        FakeRetriever(_chunks(*[0.5] * 40)),
        RecordingReranker(),
        FakeGenerator("COVERAGE: full\nReset the drive."),
        FakeAlarmStore(),
    )
    asyncio.run(orch.resolve(REQ, Tier.technician))

    assert seen == [30]


# --- the reference answers survive the pipeline -----------------------------
# reference-answers.json resolution_steps, fed back as model output. Branching
# ("If PLC: ...") is how the gold expresses alternatives, so it must not be filtered.


@pytest.mark.parametrize(
    "gold",
    [
        pytest.param(
            [
                "Record the error code (0x1001:00) and error register (0x1004:00).",
                "If it's an error (non-zero code), recover by reinitialising the EtherCAT bus "
                "or restarting the system.",
                "Interpret the 5 bytes of manufacturer-specific error data using the drive "
                "manufacturer's manual.",
                # gold says "An emergency with error code zero is informational -- just
                # acknowledge it"; the conditional form the prompt asks for:
                "If the error code is zero, just acknowledge the message.",
            ],
            id="am.fb.0002",
        ),
        pytest.param(
            [
                "Note the device name and station address in the message.",
                "Restart the system to re-initialise the EtherCAT bus.",
                "If the same device drops out again, restart (power-cycle) that drive "
                "specifically.",
            ],
            id="am.fb.0001",
        ),
        pytest.param(
            [
                "If you don't need the OPC UA server, set the configuration property "
                "opcua.enable = false.",
                "If you do need it, contact ANCA to add the OPC UA option to your license.",
            ],
            id="am.lic.0001",
        ),
        pytest.param(
            [
                "Decide whether M101 should be implemented in PLC or as an EPPL part program.",
                "If PLC: configure the M-code to a PLC mode (1-3 or 5-7), e.g. "
                "mcode.101.mode = 5.",
                "If EPPL: place m101.pp in one of the folders on the part program search "
                "hierarchy.",
                "Confirm the search hierarchy includes that folder.",
            ],
            id="am.nc.0003",
        ),
    ],
)
def test_reference_answer_steps_survive_the_pipeline(gold):
    resp = _resolve("\n".join(["COVERAGE: full", *gold]))

    assert resp.steps == gold
    assert resp.doc_coverage == "full"


def test_conditional_without_an_action_is_still_filler():
    resp = _resolve(
        "COVERAGE: partial\n"
        "Restart the system.\n"
        "If the drive is in SAFEOP, the master resets the bus.\n"
    )

    assert resp.steps == ["Restart the system."]


def test_generalised_step_that_now_repeats_another_is_collapsed():
    resp = _resolve(
        "COVERAGE: partial\n"
        "Check the drive's reported error register.\n"
        "Check the drive's reported error register (0x04).\n"
    )

    assert resp.steps == ["Check the drive's reported error register."]


def test_answer_made_only_of_example_values_has_no_coverage():
    resp = _resolve("COVERAGE: partial\nVerify the error register is 0x04.")

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
        Chunk(
            chunk_id=f"c{i}", text=f"Fault {i} is caused by broken wire number {i}.", source="m.md"
        )
        for i in range(1, 6)
    ]
    lines = [
        f"CAUSE: Fault {i} is caused by broken wire number {i}. [{i}]" for i in (1, 1, 2, 3, 4, 5)
    ]

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
MESSY_CHUNK = "\n".join(
    [
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
    ]
)
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


def test_cause_quoting_a_doc_example_is_rejected():
    # v3 bench, am.cfg.0001: the docs' data-block-mapping example returned as the cause
    example = (
        "This configuration maps process data from index 0x6040, subindex 0x00 of "
        "device 1 to the same index on devices 2, 4, and 5."
    )
    chunks = [Chunk(chunk_id="e1", text=f"{example} {CAUSED}", source="dbm.md", score=0.9)]

    resp = _resolve(_with_causes(f"CAUSE: {example}", f"CAUSE: {CAUSED}"), chunks=chunks)

    assert resp.likely_causes == [CAUSED]


def test_likely_causes_empty_when_docs_do_not_cover_alarm():
    resp = _resolve(
        f"COVERAGE: none\nThe documentation does not cover this alarm.\nCAUSE: {CAUSED} [1]"
    )

    assert resp.likely_causes == []


def test_prompt_asks_privileged_tiers_for_verbatim_causes_only():
    orch = Orchestrator(
        FakePreprocessor(), FakeRetriever([]), FakeReranker(), FakeGenerator(""), FakeAlarmStore()
    )

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
    r = client.post(
        f"{API_PREFIX}/resolve", json={"code": "am.fb.0002"}, headers=_auth(Tier.technician)
    )

    assert r.status_code == 200
    body = r.json()
    assert body["likely_causes"]
    assert body["doc_coverage"] in ("full", "partial", "none")
    assert 0.0 <= body["confidence"] <= 1.0


def test_api_operator_gets_no_causes(client):
    r = client.post(
        f"{API_PREFIX}/resolve", json={"code": "am.fb.0002"}, headers=_auth(Tier.operator)
    )

    assert r.status_code == 200
    assert r.json()["likely_causes"] == []
