"""The Server-Timing header on /resolve and /chat: stage durations in milliseconds,
kept out of the JSON body."""

import re

from rag_engine.config import API_PREFIX

STAGE = re.compile(r"^(retrieve|rerank|generate|total);dur=\d+\.\d$")


def _stages(header: str) -> list[str]:
    parts = [p.strip() for p in header.split(",")]
    assert all(STAGE.match(p) for p in parts), header
    return [p.split(";")[0] for p in parts]


def test_resolve_and_chat_send_stage_timings_in_a_header(client, bearer):
    resolve = client.post(f"{API_PREFIX}/resolve", json={"code": "am.fb.0002"}, headers=bearer)
    chat = client.post(
        f"{API_PREFIX}/chat",
        json={"conversation_id": "c1", "message": "How do I reset the drive?"},
        headers=bearer,
    )

    for r in (resolve, chat):
        assert r.status_code == 200
        assert _stages(r.headers["server-timing"]) == ["retrieve", "rerank", "generate", "total"]
        assert "stage_timings" not in r.text
