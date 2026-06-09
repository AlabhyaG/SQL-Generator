import json

from config import settings
from repositories.base import BaseRepository


class SessionRepository(BaseRepository):

    async def append_history(self, session_id: str, entry: dict) -> None:
        key = f"session:{session_id}:history"
        await self._redis.rpush(key, json.dumps(entry))
        await self._redis.expire(key, settings.session_ttl_seconds)

    async def get_history(self, session_id: str) -> list[dict]:
        entries = await self._redis.lrange(f"session:{session_id}:history", 0, -1)
        return [json.loads(e) for e in entries]

    async def save_db_url(self, session_id: str, db_url: str) -> None:
        key = f"session:{session_id}:db_url"
        await self._redis.set(key, db_url, ex=settings.session_ttl_seconds)

    async def get_db_url(self, session_id: str) -> str | None:
        return await self._redis.get(f"session:{session_id}:db_url")

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(
            f"session:{session_id}:history",
            f"session:{session_id}:db_url",
        )
