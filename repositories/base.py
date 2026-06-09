import redis.asyncio as aioredis


class BaseRepository:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis
