from graph.nodes.base import BaseNode
from graph.state import GraphState
from providers.base import BaseLLMProvider


class FormatAnswerNode(BaseNode):

    def __init__(self, llm: BaseLLMProvider) -> None:
        self._llm = llm

    def __call__(self, state: GraphState) -> dict:
        prompt = (
            f"Question: {state['question']}\n\n"
            f"Data returned by the query:\n{state['raw_results']}\n\n"
            "Write a clear, concise answer to the question using the data above. "
            "Speak directly to the user. Do not mention SQL, databases, or queries."
        )
        return {"formatted_answer": self._llm.generate(prompt).strip()}
