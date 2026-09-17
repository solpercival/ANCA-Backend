"""Redis adapter for the authentication session store."""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from redis.exceptions import RedisError

from rag_engine.api.errors import AuthUnavailable
from rag_engine.auth.interfaces import Rotation, SessionFamily, SessionStore
from rag_engine.stores.cache import get_cache_conn


class RedisSessionStore(SessionStore):
    """Store refresh-token sessions and login rate limits in the shared Redis pool."""

    async def put_token(self, digest: str, family_id: str, ttl: int) -> None:
        await self._run(lambda client: client.set(f"auth:rt:{digest}", family_id, ex=ttl))

    async def take_token(self, digest: str) -> str | None:
        return await self._run(lambda client: client.getdel(f"auth:rt:{digest}"))

    async def mark_rotated(self, digest: str, rotation: Rotation, ttl: int) -> None:
        value = json.dumps({"family_id": rotation.family_id, "rotated_at": rotation.rotated_at})
        await self._run(lambda client: client.set(f"auth:rt_used:{digest}", value, ex=ttl))

    async def get_rotation(self, digest: str) -> Rotation | None:
        value = await self._run(lambda client: client.get(f"auth:rt_used:{digest}"))
        if value is None:
            return None
        data = json.loads(value)
        return Rotation(family_id=data["family_id"], rotated_at=int(data["rotated_at"]))

    async def save_family(self, family: SessionFamily, ttl: int) -> None:
        value = json.dumps(
            {
                "family_id": family.family_id,
                "user_id": family.user_id,
                "created_at": family.created_at,
            }
        )

        def save(client: Any) -> None:
            client.set(f"auth:fam:{family.family_id}", value, ex=ttl)
            client.sadd(f"auth:user_fams:{family.user_id}", family.family_id)

        await self._run(save)

    async def get_family(self, family_id: str) -> SessionFamily | None:
        value = await self._run(lambda client: client.get(f"auth:fam:{family_id}"))
        if value is None:
            return None
        data = json.loads(value)
        return SessionFamily(
            family_id=data["family_id"],
            user_id=int(data["user_id"]),
            created_at=int(data["created_at"]),
        )

    async def revoke_family(self, family_id: str) -> None:
        def revoke(client: Any) -> None:
            value = client.get(f"auth:fam:{family_id}")
            if value is None:
                return
            user_id = json.loads(value)["user_id"]
            client.delete(f"auth:fam:{family_id}")
            client.srem(f"auth:user_fams:{user_id}", family_id)

        await self._run(revoke)

    async def revoke_user_sessions(self, user_id: int) -> None:
        def revoke(client: Any) -> None:
            index_key = f"auth:user_fams:{user_id}"
            family_ids = client.smembers(index_key)
            keys = [f"auth:fam:{family_id}" for family_id in family_ids]
            client.delete(*keys, index_key)

        await self._run(revoke)

    async def set_not_before(self, user_id: int, timestamp: int, ttl: int) -> None:
        await self._run(lambda client: client.set(f"auth:nbf:{user_id}", timestamp, ex=ttl))

    async def failed_attempts(self, key: str) -> int:
        value = await self._run(lambda client: client.get(f"auth:rl:{key}"))
        return int(value or 0)

    async def record_failed_attempt(self, key: str, window: int) -> None:
        def record(client: Any) -> None:
            redis_key = f"auth:rl:{key}"
            client.incr(redis_key)
            client.expire(redis_key, window, nx=True)

        await self._run(record)

    async def clear_failed_attempts(self, key: str) -> None:
        await self._run(lambda client: client.delete(f"auth:rl:{key}"))

    async def _run(self, operation: Callable[[Any], Any]) -> Any:
        try:
            return await asyncio.to_thread(self._run_sync, operation)
        except RedisError as exc:
            raise AuthUnavailable("Session store is unavailable") from exc

    @staticmethod
    def _run_sync(operation: Callable[[Any], Any]) -> Any:
        with get_cache_conn() as client:
            if client is None:
                raise AuthUnavailable("Session store is unavailable")
            return operation(client)
