"""Async DB methods must not block the event loop.

The psycopg pool is synchronous, so each async store method runs its query in a
worker thread (asyncio.to_thread). Each test swaps the sync helper for a blocking
sleep and fires N calls at once: run in threads they overlap and finish in about
one sleep; run on the event loop they would serialize and take N sleeps.
No Postgres is needed.
"""

import asyncio
import time

import pytest

from rag_engine.auth.user_repository import PostgresUserRepository
from rag_engine.stores.alarms import PostgresAlarmStore
from rag_engine.stores.search import PostgresDBConnection

SLEEP = 0.3
N = 5


def _blocking(result):
    def helper(*args, **kwargs):
        time.sleep(SLEEP)  # a blocking DB round-trip
        return result

    return helper


def _elapsed_for_parallel_calls(make_call) -> float:
    async def main():
        start = time.perf_counter()
        await asyncio.gather(*(make_call() for _ in range(N)))
        return time.perf_counter() - start

    return asyncio.run(main())


def _assert_concurrent(elapsed: float) -> None:
    # serialized would be N * SLEEP = 1.5s; allow generous slack for thread start-up
    assert elapsed < SLEEP * 2, f"{N} calls took {elapsed:.2f}s -- they ran one after another"


@pytest.mark.parametrize(
    "helper, call",
    [
        ("_semantic_search_sync", lambda db: db.semantic_search([0.1, 0.2], top_k=5)),
        ("_lexical_search_sync", lambda db: db.lexical_search({1: 0.5}, top_k=5)),
        ("_keyword_search_sync", lambda db: db.keyword_search("spline control points", top_k=5)),
        ("_context_search_sync", lambda db: db.context_search("conv-1")),
        ("_alarm_search_sync", lambda db: db.alarm_search({"code": "am.fb.0002", "env": {}})),
    ],
)
def test_search_methods_run_concurrently(monkeypatch, helper, call):
    monkeypatch.setattr(PostgresDBConnection, helper, _blocking([]))
    db = PostgresDBConnection()

    _assert_concurrent(_elapsed_for_parallel_calls(lambda: call(db)))


def test_search_result_passes_through_the_thread(monkeypatch):
    monkeypatch.setattr(PostgresDBConnection, "_keyword_search_sync", _blocking(["spline"]))

    assert asyncio.run(PostgresDBConnection().keyword_search("spline", top_k=5)) == ["spline"]


def test_alarm_store_runs_concurrently(monkeypatch):
    monkeypatch.setattr(PostgresAlarmStore, "_fetch_alarm_row", staticmethod(_blocking(None)))
    store = PostgresAlarmStore()

    _assert_concurrent(_elapsed_for_parallel_calls(lambda: store.get_alarm("am.fb.0002")))


def test_user_lookup_runs_concurrently(monkeypatch):
    # get_by_id runs on every authenticated request
    monkeypatch.setattr(PostgresUserRepository, "_get_by_id_sync", _blocking(None))
    users = PostgresUserRepository()

    _assert_concurrent(_elapsed_for_parallel_calls(lambda: users.get_by_id(1)))
