"""Tests for the answer-quality scores in the live eval (no API calls)."""

from pathlib import Path

import pytest
from eval.run_eval import (
    GOLD_PATH,
    content_stems,
    load_fix_terms,
    load_gold,
    score_answer,
    score_fix,
    summarize,
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

    assert scores == {"step_recall": 0.0, "actionable": 0.0, "coverage_match": 0.0}


def test_summarize_averages_answer_scores():
    base = {"hit": True, "precision": 1.0, "recall": 1.0, "reciprocal_rank": 1.0}
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


def test_summarize_reports_fix_present_only_for_listed_codes():
    base = {
        "hit": True,
        "precision": 1.0,
        "recall": 1.0,
        "reciprocal_rank": 1.0,
        "step_recall": 1.0,
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
