from langgraph.graph import END, StateGraph

from config import settings
from graph.nodes.check_confidence import CheckConfidenceNode
from graph.nodes.check_relevance import CheckRelevanceNode
from graph.nodes.execute_sql import ExecuteSQLNode
from graph.nodes.fetch_schema import FetchSchemaNode
from graph.nodes.format_answer import FormatAnswerNode
from graph.nodes.generate_sql import GenerateSQLNode
from graph.nodes.validate_sql import ValidateSQLNode
from graph.state import GraphState
from providers.base import BaseLLMProvider


# --- Routing nodes ---
# These are plain functions, not BaseNode subclasses — they only update
# state fields before re-entering generate_sql. No external calls needed.

def _set_sql_invalid(state: GraphState) -> dict:
    return {"failure_type": "sql_invalid", "retry_count": state["retry_count"] + 1}


def _set_irrelevant(state: GraphState) -> dict:
    return {
        "failure_type": "irrelevant",
        "retry_count": state["retry_count"] + 1,
        "prior_answer": state["formatted_answer"],
    }


# --- Conditional edge functions ---
# Return the name of the next node (or END) based on current state.

def _route_after_validate(state: GraphState) -> str:
    if state.get("sql_error"):
        if state["retry_count"] < settings.max_retries:
            return "set_sql_invalid"
        return END
    return "execute_sql"


def _route_after_relevance(state: GraphState) -> str:
    if state["relevance_score"] < settings.relevance_threshold:
        if state["retry_count"] < settings.max_retries:
            return "set_irrelevant"
        return END
    return "check_confidence"


# --- Graph builder ---

def build_graph(llm: BaseLLMProvider):
    g = StateGraph(GraphState)

    # Register every node
    g.add_node("fetch_schema",    FetchSchemaNode())
    g.add_node("generate_sql",    GenerateSQLNode(llm))
    g.add_node("validate_sql",    ValidateSQLNode())
    g.add_node("set_sql_invalid", _set_sql_invalid)
    g.add_node("execute_sql",     ExecuteSQLNode())
    g.add_node("format_answer",   FormatAnswerNode(llm))
    g.add_node("check_relevance", CheckRelevanceNode(llm))
    g.add_node("set_irrelevant",  _set_irrelevant)
    g.add_node("check_confidence", CheckConfidenceNode(llm))

    # Entry point
    g.set_entry_point("fetch_schema")

    # Fixed edges — always go to this next node
    g.add_edge("fetch_schema",    "generate_sql")
    g.add_edge("generate_sql",    "validate_sql")
    g.add_edge("set_sql_invalid", "generate_sql")
    g.add_edge("execute_sql",     "format_answer")
    g.add_edge("format_answer",   "check_relevance")
    g.add_edge("set_irrelevant",  "generate_sql")
    g.add_edge("check_confidence", END)

    # Conditional edges — routing function decides the next node at runtime
    g.add_conditional_edges("validate_sql",    _route_after_validate)
    g.add_conditional_edges("check_relevance", _route_after_relevance)

    return g.compile()
