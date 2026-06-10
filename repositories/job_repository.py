import json

from config import settings
from repositories.base import BaseRepository

_OPTIONAL_FIELDS = ("answer", "sql_query", "confidence", "error", "failure_type", "clarification")


class JobRepository(BaseRepository):

    async def create(self, job_id: str, question: str, session_id: str) -> None:
        key = f"job:{job_id}"
        await self._redis.hset(key, mapping={
            "job_id": job_id,
            "status": "queued",
            "question": question,
            "session_id": session_id,
            "retry_count": "0",
            "can_retry": "false",
        })
        await self._redis.expire(key, settings.job_ttl_seconds)

    async def get(self, job_id: str) -> dict | None:
        data = await self._redis.hgetall(f"job:{job_id}")
        if not data:
            return None
        return self._deserialize(data)

    async def update(self, job_id: str, **fields) -> None:
        mapping = {}
        for k, v in fields.items():
            if v is None:
                mapping[k] = ""
            elif isinstance(v, bool):
                mapping[k] = "true" if v else "false"
            else:
                mapping[k] = str(v)
        await self._redis.hset(f"job:{job_id}", mapping=mapping)

    async def enqueue(self, job_id: str, session_id: str, question: str, db_url: str, feedback: str | None = None) -> None:
        payload = json.dumps({
            "job_id": job_id,
            "session_id": session_id,
            "question": question,
            "db_url": db_url,
            "feedback": feedback,
        })
        await self._redis.rpush("queue:jobs", payload)

    def _deserialize(self, data: dict) -> dict:
        result = dict(data)
        result["retry_count"] = int(result.get("retry_count", 0))
        result["can_retry"] = result.get("can_retry", "false") == "true"
        for field in _OPTIONAL_FIELDS:
            if result.get(field) == "":
                result[field] = None
        # clarification is stored as JSON string, deserialize back to list
        if result.get("clarification"):
            try:
                result["clarification"] = json.loads(result["clarification"])
            except Exception:
                result["clarification"] = None
        return result
