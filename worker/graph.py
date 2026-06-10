from langgraph.graph import END, StateGraph

from config import settings
from graph.nodes.ambiguity_check import AmbiguityCheckNode
from graph.nodes.check_confidence import CheckConfidenceNode
from graph.nodes.check_relevance import CheckRelevanceNode
from graph.nodes.execute_sql import ExecuteSQLNode
from graph.nodes.fetch_schema import FetchSchemaNode
from graph.nodes.format_answer import FormatAnswerNode
from graph.nodes.generate_sql import GenerateSQLNode
from graph.nodes.retrieve_tables import RetrieveTablesNode
from graph.nodes.validate_sql import ValidateSQLNode
from graph.schema_retriever import SchemaRetriever
from graph.state import GraphState
from providers.base import BaseLLMProvider


def _set_sql_invalid(state: GraphState) -> dict:
    return {"failure_type": "sql_invalid", "retry_count": state["retry_count"] + 1}


def _set_irrelevant(state: GraphState) -> dict:
    return {
        "failure_type": "irrelevant",
        "retry_count": state["retry_count"] + 1,
        "prior_answer": state["formatted_answer"],
    }


def _route_after_ambiguity(state: GraphState) -> str:
    if state.get("ambiguous_groups"):
        return END
    return "generate_sql"


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


def build_graph(llm: BaseLLMProvider, retriever: SchemaRetriever):
    g = StateGraph(GraphState)

    g.add_node("fetch_schema",     FetchSchemaNode(retriever))
    g.add_node("retrieve_tables",  RetrieveTablesNode(retriever))
    g.add_node("ambiguity_check",  AmbiguityCheckNode())
    g.add_node("generate_sql",     GenerateSQLNode(llm))
    g.add_node("validate_sql",     ValidateSQLNode())
    g.add_node("set_sql_invalid",  _set_sql_invalid)
    g.add_node("execute_sql",      ExecuteSQLNode())
    g.add_node("format_answer",    FormatAnswerNode(llm))
    g.add_node("check_relevance",  CheckRelevanceNode(llm))
    g.add_node("set_irrelevant",   _set_irrelevant)
    g.add_node("check_confidence", CheckConfidenceNode(llm))

    g.set_entry_point("fetch_schema")

    # Fixed edges
    g.add_edge("fetch_schema",    "retrieve_tables")
    g.add_edge("retrieve_tables", "ambiguity_check")
    g.add_edge("generate_sql",    "validate_sql")
    g.add_edge("set_sql_invalid", "generate_sql")
    g.add_edge("execute_sql",     "format_answer")
    g.add_edge("format_answer",   "check_relevance")
    g.add_edge("set_irrelevant",  "generate_sql")
    g.add_edge("check_confidence", END)

    # Conditional edges
    g.add_conditional_edges("ambiguity_check", _route_after_ambiguity)
    g.add_conditional_edges("validate_sql",    _route_after_validate)
    g.add_conditional_edges("check_relevance", _route_after_relevance)

    return g.compile()
