import re

from graph.nodes.base import BaseNode
from graph.state import GraphState
from providers.base import BaseLLMProvider


class CheckRelevanceNode(BaseNode):

    def __init__(self, llm: BaseLLMProvider) -> None:
        self._llm = llm

    def __call__(self, state: GraphState) -> dict:
        prompt = (
            f"Question: {state['question']}\n\n"
            f"Answer: {state['formatted_answer']}\n\n"
            "Rate how well this answer addresses the question. "
            "Respond with ONLY a single number between 0.0 and 1.0. "
            "1.0 = fully answers the question. 0.0 = completely unrelated."
        )
        response = self._llm.generate(prompt).strip()
        return {"relevance_score": self._parse_score(response)}

    def _parse_score(self, response: str) -> float:
        match = re.search(r"\d+\.?\d*", response)
        if match:
            return min(1.0, max(0.0, float(match.group())))
        return 0.0
