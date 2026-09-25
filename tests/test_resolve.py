def test_resolve_returns_steps_and_citations(client, bearer):
    r = client.post("/api/v2/resolve", json={"code": "am.fb.0002"}, headers=bearer)
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "am.fb.0002"
    assert len(body["steps"]) >= 1
    assert len(body["citations"]) >= 1


def test_resolve_rejects_invalid_alarm_code_format(client, bearer):
    r = client.post("/api/v2/resolve", json={"code": "BADCODE"}, headers=bearer)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_resolve_rejects_invalid_alarm_code_separator(client, bearer):
    r = client.post("/api/v2/resolve", json={"code": "am5fb50002"}, headers=bearer)
    assert r.status_code == 422


def test_chat_rejects_message_over_max_length(client, bearer):
    r = client.post(
        "/api/v2/chat",
        json={"conversation_id": "c-1", "message": "x" * 6000},
        headers=bearer,
    )
    assert r.status_code == 422


def test_chat_rejects_oversized_request_body(client, bearer):
    r = client.post(
        "/api/v2/chat",
        json={"conversation_id": "c-1", "message": "x" * 200000},
        headers=bearer,
    )
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"
