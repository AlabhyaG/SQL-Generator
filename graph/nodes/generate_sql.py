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
        parts = [
            "You are a SQL expert. Generate a single PostgreSQL query for the question below.",
            "Return ONLY the raw SQL — no explanation, no markdown, no code fences.",
            "",
            f"Schema:\n{state['db_schema']}",
            "",
            f"Question: {state['question']}",
        ]

        if state.get("session_history"):
            history = "\n".join(
                f"Q: {h['question']}\nA: {h['answer']}"
                for h in state["session_history"][-3:]
            )
            parts.insert(4, f"Recent conversation:\n{history}\n")

        if state.get("failure_type") == "sql_invalid" and state.get("sql_error"):
            parts.append(f"\nPrevious query failed with: {state['sql_error']}\nFix the error.")

        if state.get("failure_type") == "irrelevant":
            parts.append("\nYour previous answer did not address the question. Try a different approach.")

        if state.get("feedback"):
            parts.append(f"\nUser feedback: {state['feedback']}")

        return "\n".join(parts)

    def _extract_sql(self, response: str) -> str:
        match = re.search(r"```(?:sql)?\s*(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
