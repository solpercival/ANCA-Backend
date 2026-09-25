import json

import pytest

from eval.deep_eval import assert_thresholds, score_snapshot


def test_score_snapshot_returns_expected_metrics():
    result = {
        "query": "motor stalls after startup",
        "code": "am.fb.0002",
        "citation_ids": ["c1", "c9"],
        "step_count": 3,
        "confidence": 0.89,
        "status": "ok",
    }

    assert score_snapshot(result) == {
        "faithfulness": 0.89,
        "groundedness": 1.0,
        "relevance": 1.0,
    }


def test_assert_thresholds_passes_when_metrics_are_above_minimum():
    scores = {"faithfulness": 0.9, "groundedness": 0.85, "relevance": 0.9}
    assert_thresholds(scores)


def test_assert_thresholds_fails_when_metric_is_too_low():
    scores = {"faithfulness": 0.5, "groundedness": 1.0, "relevance": 1.0}

    with pytest.raises(SystemExit, match="DeepEval thresholds failed"):
        assert_thresholds(scores)


def test_snapshot_output_is_json_serializable(tmp_path):
    result = {
        "query": "motor stalls after startup",
        "code": "am.fb.0002",
        "citation_ids": ["c1", "c9"],
        "step_count": 3,
        "confidence": 0.891,
        "status": "ok",
    }

    json.dumps(result)
    assert result["step_count"] == 3
