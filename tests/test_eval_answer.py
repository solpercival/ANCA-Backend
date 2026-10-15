"""Tests for the answer-quality scores in the live eval (no API calls)."""

from pathlib import Path

import pytest
from eval.run_eval import (
    FIX_TERMS_PATH,
    GOLD_PATH,
    average_results,
    below_minimums,
    content_stems,
    load_fix_terms,
    load_gold,
    score_answer,
    score_fix,
    summarize,
    summarize_runs,
)

GOLD = {
    "resolution_steps": [
        "Restart the system to re-initialise the EtherCAT bus.",
        "If the same device drops out again, restart (power-cycle) that drive.",
    ],
    "doc_coverage": "full",
}


def test_content_stems_ignore_stopwords_and_match_word_forms():
    assert content_stems("Restarting the drive") == content_stems("restart drive")
    assert "the" not in content_stems("the bus")


def test_actionable_steps_score_high():
    answer = {
        "steps": [
            "Restart the system to reinitialise the EtherCAT bus.",
            "Power-cycle the drive if the device drops out again.",
        ],
        "doc_coverage": "full",
    }

    scores = score_answer(answer, GOLD)

    assert scores["actionable"] == 1.0
    assert scores["coverage_match"] == 1.0
    assert scores["step_recall"] > 0.6


def test_conditional_steps_count_as_actionable():
    # the gold answers branch: "If PLC: configure ...", "If you do need it, contact ..."
    answer = {
        "steps": [
            "If the same device drops out again, restart (power-cycle) that drive.",
            "If PLC: configure the M-code to a PLC mode.",
            "If the device drops out, the master resets the bus.",  # no action
        ],
        "doc_coverage": "full",
    }

    assert score_answer(answer, GOLD)["actionable"] == pytest.approx(2 / 3)


def test_restating_the_alarm_scores_low():
    # the pattern the bench showed: describing the alarm instead of fixing it
    answer = {
        "steps": ["Fieldbus device Drive_3 is in SAFEOP but expected to be in OP state."],
        "doc_coverage": "partial",
    }

    scores = score_answer(answer, GOLD)

    assert scores["actionable"] == 0.0
    assert scores["coverage_match"] == 0.0
    assert scores["step_recall"] < 0.3


def test_empty_answer_scores_zero():
    scores = score_answer({"steps": []}, GOLD)

    assert scores == {
        "step_recall": 0.0,
        "step_precision": 0.0,
        "length_ratio": 0.0,
        "actionable": 0.0,
        "coverage_match": 0.0,
    }


def test_padding_lowers_step_precision_but_not_step_recall():
    """step_recall cannot see padding: the gold words are all there either way."""
    fix = [
        "Restart the system to reinitialise the EtherCAT bus.",
        "If the same device drops out again, power-cycle that drive.",
    ]
    padding = [
        "Check the G_DD_COE_DRIVE_STATE_ACTUAL3 diagnostic variable.",
        "Verify the expected operational state defined by the master.",
    ]

    exact = score_answer({"steps": fix}, GOLD)
    padded = score_answer({"steps": fix + padding}, GOLD)

    assert padded["step_recall"] == exact["step_recall"]
    assert (exact["step_precision"], exact["length_ratio"]) == (1.0, 1.0)
    assert (padded["step_precision"], padded["length_ratio"]) == (0.5, 2.0)


def test_several_passes_are_averaged_and_their_spread_reported():
    base = {
        "hit": True,
        "precision": 1.0,
        "recall": 1.0,
        "reciprocal_rank": 1.0,
        "length_ratio": 1.0,
        "actionable": 1.0,
        "coverage_match": 1.0,
        "code": "am.fb.0001",
        "doc_coverage": "full",
    }
    first = [{**base, "step_recall": 0.4, "step_precision": 0.5, "steps": ["Restart."]}]
    second = [{**base, "step_recall": 0.6, "step_precision": 1.0, "steps": ["Reset."]}]

    summary = summarize_runs([first, second])
    merged = average_results([first, second])

    assert summary["step_precision"] == 0.75
    assert summary["range"]["step_precision"] == [0.5, 1.0]
    assert summary["runs"] == 2
    assert merged[0]["step_recall"] == 0.5
    assert merged[0]["steps"] == ["Restart."]
    # one pass is the plain summary, with no range
    assert "range" not in summarize_runs([first])


def test_scores_below_their_minimum_are_reported():
    summary = {"fix_present": 0.682, "hit": 0.909}

    assert below_minimums(summary, "fix_present=0.68, hit=0.9") == []
    assert below_minimums(summary, "fix_present=0.7,hit=0.9") == [("fix_present", 0.682, 0.7)]
    # a misspelt score name must not pass silently
    assert below_minimums(summary, "fix_presnt=0.1") == [("fix_presnt", None, 0.1)]
    assert below_minimums(summary, None) == []


def test_summarize_averages_answer_scores():
    base = {
        "hit": True,
        "precision": 1.0,
        "recall": 1.0,
        "reciprocal_rank": 1.0,
        "step_precision": 1.0,
        "length_ratio": 1.0,
    }
    results = [
        {**base, "step_recall": 1.0, "actionable": 1.0, "coverage_match": 1.0},
        {**base, "step_recall": 0.0, "actionable": 0.5, "coverage_match": 0.0},
    ]

    summary = summarize(results)

    assert summary["step_recall"] == 0.5
    assert summary["actionable"] == 0.75
    assert summary["coverage_match"] == 0.5


def test_fix_present_when_the_resolving_action_is_given():
    # am.lic.0001's fix is disable the server OR get the licence
    groups = [["false", "disable"], ["licen", "anca"]]

    assert score_fix(["Set opcua.enable to false.", "Contact ANCA for a licence."], groups) == 1.0
    assert score_fix(["Set opcua.enable to false."], groups) == 0.5


def test_fix_absent_when_steps_only_check_things():
    # the bench's am.lic.0001 answer: checks, and the opposite of the fix
    steps = [
        "Check if OPC UA server is enabled in configuration",
        'Verify the "opcua.enable" property is set to true',
    ]

    assert score_fix(steps, [["false", "disable"], ["licen", "anca"]]) == 0.0


def test_nc_0005_fix_is_recognised_in_other_words_than_the_gold_answer():
    # scored 0.0 for three days on an answer that gave the fix: only "split",
    # "separate block" and "remove duplicate class 1" were accepted
    if not FIX_TERMS_PATH.exists():
        pytest.skip("fix terms file not present")
    groups = load_fix_terms()["am.nc.0005"]

    # the two answers the 8B generator alternates between
    reworded = [
        "Edit the program to ensure only one class 1 preparatory word is used per block."
    ]
    removes = ["Edit the program to remove all but one class 1 preparatory word from the block."]
    extras = ["Remove any additional class 1 preparatory words from the block"]
    checks_only = ["Check which preparatory words in the block belong to class 1."]

    assert score_fix(reworded, groups) == 1.0
    assert score_fix(removes, groups) == 1.0
    assert score_fix(extras, groups) == 1.0
    assert score_fix(checks_only, groups) == 0.0


def test_lic_0001_fix_terms_do_not_reward_the_opposite_fix():
    # bench at temperature 0 scored this 1.0: "false" matched the certificate
    # setting and "anca" matched the certificate subject
    if not FIX_TERMS_PATH.exists():
        pytest.skip("fix terms file not present")
    groups = load_fix_terms()["am.lic.0001"]
    harmful = [
        "Set opcua.enable to true",
        "Check the opcua.enable configuration property value",
        "Ensure the opcua.certificate.autogenerate is set to false",
        "Verify the opcua.certificate.subject matches CN=ANCA Motion AMCore OPC UA Server",
    ]
    gold = [
        "If you don't need the OPC UA server, set the configuration property "
        "opcua.enable = false.",
        "If you do need it, contact ANCA to add the OPC UA option to your license.",
    ]

    assert score_fix(harmful, groups) == 0.0
    assert score_fix(gold, groups) == 1.0
    assert (
        score_fix(
            ["Disable the OPC UA server by setting the opcua.enable configuration "
             "property to false."],
            groups,
        )
        == 0.5
    )


def test_summarize_reports_fix_present_only_for_listed_codes():
    base = {
        "hit": True,
        "precision": 1.0,
        "recall": 1.0,
        "reciprocal_rank": 1.0,
        "step_recall": 1.0,
        "step_precision": 1.0,
        "length_ratio": 1.0,
        "actionable": 1.0,
        "coverage_match": 1.0,
    }
    results = [{**base, "fix_present": 1.0}, {**base, "fix_present": 0.5}, base]

    summary = summarize(results)

    assert summary["fix_present"] == 0.75
    assert summary["fix_solved"] == 1


def test_every_gold_code_has_fix_terms():
    # the gold file lives in the docs submodule, which hosted CI may not check out
    if not Path(GOLD_PATH).exists():
        pytest.skip("docs submodule not checked out")
    gold = load_gold(GOLD_PATH)

    assert set(load_fix_terms()) == set(gold)
