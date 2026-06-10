import re

from graph.nodes.base import BaseNode
from graph.state import GraphState
from providers.base import BaseLLMProvider


class GenerateSQLNode(BaseNode):

    def __init__(self, llm: BaseLLMProvider) -> None:
        self._llm = llm

    def __call__(self, state: GraphState) -> dict:
        prompt = self._build_prompt(state)
        response = self._llm.generate(prompt)
        return {"sql_query": self._extract_sql(response), "sql_error": None}

    def _build_prompt(self, state: GraphState) -> str:
        schema = state.get("filtered_schema") or state["db_schema"]
        relevant = set(state.get("relevant_tables", []))
        metadata = state.get("schema_metadata", {})

        parts = [
            "You are a SQL expert. Generate a single PostgreSQL query for the question below.",
            "Return ONLY the raw SQL — no explanation, no markdown, no code fences.",
            "",
            f"Schema:\n{schema}",
        ]

        # Relationship hints
        hints = self._build_hints(relevant, metadata)
        if hints:
            parts.append("\nRelationships:\n" + "\n".join(f"  - {h}" for h in hints))

        parts.append(f"\nQuestion: {state['question']}")

        if state.get("session_history"):
            history = "\n".join(
                f"Q: {h['question']}\nA: {h['answer']}"
                for h in state["session_history"][-3:]
            )
            parts.append(f"\nRecent conversation:\n{history}")

        if state.get("failure_type") == "sql_invalid" and state.get("sql_error"):
            parts.append(f"\nPrevious query failed with: {state['sql_error']}\nFix the error.")

        if state.get("failure_type") == "irrelevant":
            parts.append("\nYour previous answer did not address the question. Try a different approach.")

        if state.get("feedback"):
            parts.append(f"\nUser clarification: {state['feedback']}")

        return "\n".join(parts)

    def _build_hints(self, relevant: set[str], metadata: dict) -> list[str]:
        hints = []

        # Shared join keys across relevant tables
        for col, tables in metadata.get("shared_columns", {}).items():
            in_relevant = [t for t in tables if t in relevant]
            if len(in_relevant) >= 2:
                hints.append(
                    f"'{col}' is a shared key across: {', '.join(in_relevant)} — use it for JOINs"
                )

        # Column equivalences across relevant tables
        for eq in metadata.get("equivalences", []):
            if eq["table1"] in relevant or eq["table2"] in relevant:
                hints.append(
                    f"'{eq['col1']}' in {eq['table1']} is equivalent to "
                    f"'{eq['col2']}' in {eq['table2']}"
                )

        return hints

    def _extract_sql(self, response: str) -> str:
        match = re.search(r"```(?:sql)?\s*(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
