import redis.asyncio as aioredis
from fastapi import Depends, Request

from repositories.job_repository import JobRepository
from repositories.session_repository import SessionRepository


def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis


def get_job_repo(redis: aioredis.Redis = Depends(get_redis)) -> JobRepository:
    return JobRepository(redis)


def get_session_repo(redis: aioredis.Redis = Depends(get_redis)) -> SessionRepository:
    return SessionRepository(redis)
