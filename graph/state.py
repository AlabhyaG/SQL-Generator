from typing import TypedDict


class GraphState(TypedDict):
    question: str
    session_history: list
    db_url: str
    db_schema: str                  # full compressed schema (fallback)
    schema_metadata: dict           # groups, shared_columns, equivalences
    relevant_tables: list[str]      # tables retrieved by RAG for this question
    filtered_schema: str            # schema string with only relevant tables
    ambiguous_groups: list          # table groups that caused ambiguity
    sql_query: str
    sql_error: str | None
    raw_results: list
    formatted_answer: str
    relevance_score: float
    confidence_score: float
    retry_count: int
    failure_type: str | None
    feedback: str | None
    prior_answer: str | None
