from typing import Literal

from pydantic import BaseModel


class AmbiguousTable(BaseModel):
    name: str
    columns: list[str]


class AmbiguousGroup(BaseModel):
    tables: list[AmbiguousTable]
    note: str


class JobResult(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed", "needs_clarification"]
    question: str
    answer: str | None = None
    sql_query: str | None = None
    confidence: Literal["high", "low"] | None = None
    can_retry: bool = False
    error: str | None = None
    retry_count: int = 0
    clarification: list[AmbiguousGroup] | None = None
