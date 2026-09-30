from contextlib import contextmanager

import pytest

from rag_engine.auth.interfaces import Rotation, SessionFamily
from rag_engine.auth.session_store import RedisSessionStore


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}
        self.expirations = {}

    def set(self, key, value, ex=None):
        self.values[key] = str(value)
        if ex is not None:
            self.expirations[key] = ex

    def get(self, key):
        return self.values.get(key)

    def getdel(self, key):
        return self.values.pop(key, None)

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.sets.pop(key, None)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set()).copy()

    def srem(self, key, value):
        self.sets.get(key, set()).discard(value)

    def incr(self, key):
        self.values[key] = str(int(self.values.get(key, 0)) + 1)

    def expire(self, key, seconds, nx=False):
        if not nx or key not in self.expirations:
            self.expirations[key] = seconds


@pytest.fixture
def store(monkeypatch):
    redis = FakeRedis()

    @contextmanager
    def fake_connection():
        yield redis

    monkeypatch.setattr("rag_engine.auth.session_store.get_cache_conn", fake_connection)
    return RedisSessionStore(), redis


@pytest.mark.asyncio
async def test_refresh_token_is_consumed_once(store):
    session_store, _ = store

    await session_store.put_token("digest", "family-1", ttl=60)

    assert await session_store.take_token("digest") == "family-1"
    assert await session_store.take_token("digest") is None


@pytest.mark.asyncio
async def test_rotation_and_family_round_trip_and_revoke(store):
    session_store, redis = store
    rotation = Rotation(family_id="family-1", rotated_at=123)
    family = SessionFamily(family_id="family-1", user_id=7, created_at=100)

    await session_store.mark_rotated("digest", rotation, ttl=60)
    await session_store.save_family(family, ttl=300)

    assert await session_store.get_rotation("digest") == rotation
    assert await session_store.get_family("family-1") == family
    assert redis.sets["auth:user_fams:7"] == {"family-1"}

    await session_store.revoke_family("family-1")

    assert await session_store.get_family("family-1") is None
    assert redis.sets["auth:user_fams:7"] == set()


@pytest.mark.asyncio
async def test_revoke_user_sessions_removes_all_families(store):
    session_store, _ = store
    families = [
        SessionFamily(family_id="family-1", user_id=7, created_at=100),
        SessionFamily(family_id="family-2", user_id=7, created_at=101),
    ]

    for family in families:
        await session_store.save_family(family, ttl=300)

    await session_store.revoke_user_sessions(7)

    assert await session_store.get_family("family-1") is None
    assert await session_store.get_family("family-2") is None


@pytest.mark.asyncio
async def test_failed_attempts_can_be_recorded_and_cleared(store):
    session_store, redis = store

    assert await session_store.failed_attempts("ip:1") == 0
    await session_store.record_failed_attempt("ip:1", window=60)
    await session_store.record_failed_attempt("ip:1", window=60)

    assert await session_store.failed_attempts("ip:1") == 2
    assert redis.expirations["auth:rl:ip:1"] == 60

    await session_store.clear_failed_attempts("ip:1")

    assert await session_store.failed_attempts("ip:1") == 0