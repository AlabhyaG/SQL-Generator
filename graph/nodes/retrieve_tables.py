from graph.nodes.base import BaseNode
from graph.schema_retriever import SchemaRetriever
from graph.state import GraphState


class RetrieveTablesNode(BaseNode):

    def __init__(self, retriever: SchemaRetriever) -> None:
        self._retriever = retriever

    def __call__(self, state: GraphState) -> dict:
        relevant = self._retriever.retrieve(state["db_url"], state["question"], k=5)

        # Fall back to full schema if retrieval returns nothing
        if not relevant:
            return {
                "relevant_tables": [],
                "filtered_schema": state["db_schema"],
            }

        compressed = state["schema_metadata"]["compressed"]
        filtered = "\n".join(
            f"{table}({', '.join(compressed[table])})"
            for table in relevant
            if table in compressed
        )

        return {
            "relevant_tables": relevant,
            "filtered_schema": filtered,
        }
