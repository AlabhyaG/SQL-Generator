from pydantic import BaseModel


class HistoryEntry(BaseModel):
    question: str
    answer: str
    sql: str
    confidence: str
    timestamp: str


class SessionHistory(BaseModel):
    session_id: str
    entries: list[HistoryEntry]
