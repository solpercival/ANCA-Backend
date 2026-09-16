from rag_engine.config import get_settings


def test_resolve_limit_returns_retry_after(client, bearer, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "resolve_rate_limit_per_ip", 1)
    monkeypatch.setattr(settings, "resolve_rate_limit_per_tier", 100)

    first = client.post("/api/v1/resolve", json={"code": "am.fb.0002"}, headers=bearer)
    second = client.post("/api/v1/resolve", json={"code": "am.fb.0002"}, headers=bearer)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"].isdigit()
    assert int(second.headers["retry-after"]) > 0
    assert second.json()["error"]["code"] == "rate_limited"


def test_resolve_and_chat_have_separate_buckets(client, bearer, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "resolve_rate_limit_per_ip", 1)
    monkeypatch.setattr(settings, "resolve_rate_limit_per_tier", 100)
    monkeypatch.setattr(settings, "chat_rate_limit_per_ip", 1)
    monkeypatch.setattr(settings, "chat_rate_limit_per_tier", 100)

    resolve = client.post("/api/v1/resolve", json={"code": "am.fb.0002"}, headers=bearer)
    chat = client.post(
        "/api/v1/chat",
        json={"conversation_id": "test-conversation", "message": "How do I reset the drive?"},
        headers=bearer,
    )

    assert resolve.status_code == 200
    assert chat.status_code == 200


def test_rate_limit_fails_closed_without_backend(client, bearer):
    del client.app.state.rate_limit_backend
    response = client.post("/api/v1/resolve", json={"code": "am.fb.0002"}, headers=bearer)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "rate_limit_unavailable"