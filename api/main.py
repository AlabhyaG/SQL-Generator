from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from api.routes import jobs, query, sessions
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    yield
    await app.state.redis.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SQL Generator",
        description="Plain English to SQL using LLMs",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(query.router)
    app.include_router(jobs.router)
    app.include_router(sessions.router)

    return app


app = create_app()
