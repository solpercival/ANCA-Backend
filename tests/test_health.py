"""Liveness endpoint, the standard error body for unknown routes, and that
resolve rejects unauthenticated calls.
"""

from rag_engine.config import API_PREFIX


def test_health(client):
    r = client.get(f"{API_PREFIX}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_missing_route_uses_standard_error_payload(client):
    r = client.get("/definitely-not-a-real-route")
    assert r.status_code == 404
    payload = r.json()
    assert payload["error"]["code"] == "not_found"


def test_resolve_requires_auth(client):
    r = client.post(f"{API_PREFIX}/resolve", json={"code": "am.fb.0002"})
    assert r.status_code == 401
