from typing import TypedDict


class GraphState(TypedDict):
    question: str
    session_history: list           # list of {question, answer, sql, confidence} dicts
    db_url: str
    db_schema: str
    sql_query: str
    sql_error: str | None
    raw_results: list
    formatted_answer: str
    relevance_score: float
    confidence_score: float
    retry_count: int
    failure_type: str | None        # "sql_invalid" | "irrelevant" | "low_confidence"
    feedback: str | None            # user clarification from a prior low-confidence answer
    prior_answer: str | None        # the answer that was flagged as low-confidence
