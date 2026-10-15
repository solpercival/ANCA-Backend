"""Offline snapshot helpers in eval/run_eval.py: result normalization and
the mismatch check used by the rag-snapshot workflow.
"""

import json

from eval.run_eval import compare_snapshot, normalize_result


def test_normalize_result_keeps_structured_fields_stable():
    payload = {
        "query": "motor stalls after startup",
        "code": "am.fb.0002",
        "steps": ["Check power", "Inspect drive", "Verify wiring"],
        "citations": [
            {"doc": "Documentation", "path": "manual.md", "section": "Drive"},
            {"doc": "Documentation", "path": "faq.md", "section": None},
        ],
        "confidence": 0.891234,
        "status": "ok",
    }

    assert normalize_result(payload) == {
        "query": "motor stalls after startup",
        "code": "am.fb.0002",
        "citation_paths": ["manual.md", "faq.md"],
        "step_count": 3,
        "confidence": 0.891,
        "status": "ok",
    }


def test_compare_snapshot_detects_a_true_mismatch(tmp_path):
    generated = tmp_path / "generated.json"
    expected = tmp_path / "expected.json"

    generated.write_text(
        json.dumps(
            {
                "query": "A",
                "code": "x",
                "citation_paths": ["manual.md"],
                "step_count": 1,
                "confidence": 0.8,
                "status": "ok",
            }
        ),
        encoding="utf-8",
    )
    expected.write_text(
        json.dumps(
            {
                "query": "A",
                "code": "x",
                "citation_paths": ["faq.md"],
                "step_count": 1,
                "confidence": 0.8,
                "status": "ok",
            }
        ),
        encoding="utf-8",
    )

    try:
        compare_snapshot(generated, expected)
    except SystemExit as exc:
        assert "Snapshot mismatch" in str(exc)
    else:
        raise AssertionError("compare_snapshot should fail when expected and generated differ")
