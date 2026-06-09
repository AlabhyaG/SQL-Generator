from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    db_url: str
    session_id: str | None = None
    feedback: str | None = None


class QueryResponse(BaseModel):
    job_id: str
    session_id: str
    status: str = Field(default="queued")
