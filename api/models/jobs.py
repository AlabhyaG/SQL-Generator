from typing import Literal

from pydantic import BaseModel


class JobResult(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    question: str
    answer: str | None = None
    sql_query: str | None = None
    confidence: Literal["high", "low"] | None = None
    can_retry: bool = False
    error: str | None = None
    retry_count: int = 0
