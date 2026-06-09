import asyncio
import json
from datetime import datetime, timezone

import redis.asyncio as aioredis

from config import settings
from providers.gemini import GeminiLLMProvider
from repositories.job_repository import JobRepository
from repositories.session_repository import SessionRepository
from worker.graph import build_graph


async def _process_job(
    payload: dict,
    job_repo: JobRepository,
    session_repo: SessionRepository,
    graph,
) -> None:
    job_id = payload["job_id"]
    session_id = payload["session_id"]

    await job_repo.update(job_id, status="running")

    try:
        history = await session_repo.get_history(session_id)

        initial_state = {
            "question": payload["question"],
            "db_url": payload["db_url"],
            "session_history": history,
            "db_schema": "",
            "sql_query": "",
            "sql_error": None,
            "raw_results": [],
            "formatted_answer": "",
            "relevance_score": 0.0,
            "confidence_score": 0.0,
            "retry_count": 0,
            "failure_type": None,
            "feedback": payload.get("feedback"),
            "prior_answer": None,
        }

        final_state = graph.invoke(initial_state)

        exhausted = final_state["retry_count"] >= settings.max_retries and (
            final_state.get("sql_error") or final_state.get("failure_type") == "irrelevant"
        )

        if exhausted:
            await job_repo.update(
                job_id,
                status="failed",
                failure_type=final_state.get("failure_type"),
                error=final_state.get("sql_error") or "Answer was not relevant after max retries",
                retry_count=final_state["retry_count"],
            )
            return

        confidence = "high" if final_state["confidence_score"] >= settings.confidence_threshold else "low"

        await job_repo.update(
            job_id,
            status="completed",
            answer=final_state["formatted_answer"],
            sql_query=final_state["sql_query"],
            confidence=confidence,
            can_retry=confidence == "low",
            retry_count=final_state["retry_count"],
        )

        # Only record high-confidence answers in session history
        if confidence == "high":
            await session_repo.append_history(session_id, {
                "question": payload["question"],
                "answer": final_state["formatted_answer"],
                "sql": final_state["sql_query"],
                "confidence": confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    except Exception as e:
        await job_repo.update(job_id, status="failed", error=str(e))


async def run() -> None:
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    job_repo = JobRepository(redis_client)
    session_repo = SessionRepository(redis_client)

    llm = GeminiLLMProvider()
    graph = build_graph(llm)

    print("Worker started — listening on queue:jobs")

    while True:
        result = await redis_client.blpop("queue:jobs", timeout=0)
        if result is None:
            continue
        _, raw = result
        payload = json.loads(raw)
        print(f"Processing job {payload['job_id']}")
        await _process_job(payload, job_repo, session_repo, graph)


if __name__ == "__main__":
    asyncio.run(run())
