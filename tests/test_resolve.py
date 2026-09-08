def test_resolve_returns_steps_and_citations(client, bearer):
    r = client.post("/api/v1/resolve", json={"code": "am.fb.0002"}, headers=bearer)
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "am.fb.0002"
    assert len(body["steps"]) >= 1
    assert len(body["citations"]) >= 1
