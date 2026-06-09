from abc import ABC, abstractmethod

from graph.state import GraphState


class BaseNode(ABC):

    @abstractmethod
    def __call__(self, state: GraphState) -> dict:
        """Receive full state, return a dict of only the fields that changed."""
