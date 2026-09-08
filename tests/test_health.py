def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_resolve_requires_auth(client):
    r = client.post("/api/v1/resolve", json={"code": "am.fb.0002"})
    assert r.status_code == 401
