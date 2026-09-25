"""Test Prometheus metrics exposition."""
import pytest


def test_metrics_endpoint_available(client):
    """Verify /metrics endpoint is accessible and returns 200."""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")


def test_metrics_contains_fastapi_metrics(client):
    """Verify FastAPI auto-instrumented metrics are present in output."""
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_request_duration_seconds" in r.text


def test_rag_metrics_incremented_after_resolve(client, bearer):
    """Verify resolve call records RAG metrics."""
    # Call resolve to trigger metric recording
    r = client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=bearer)
    assert r.status_code == 200

    # Check metrics contain our custom RAG metrics
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "rag_stage_seconds_bucket" in r.text
    assert "rag_resolve_total" in r.text
    assert 'outcome="ok"' in r.text

