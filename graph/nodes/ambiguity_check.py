from graph.nodes.base import BaseNode
from graph.state import GraphState


class AmbiguityCheckNode(BaseNode):

    def __call__(self, state: GraphState) -> dict:
        # If user already gave feedback about which table to use, skip ambiguity check
        if state.get("feedback"):
            return {"ambiguous_groups": []}

        relevant = set(state.get("relevant_tables", []))
        groups = state.get("schema_metadata", {}).get("groups", [])

        ambiguous = []
        for group in groups:
            in_group = set([group["primary"]] + group["variants"])
            overlap = relevant & in_group
            if len(overlap) >= 2:
                compressed = state["schema_metadata"]["compressed"]
                ambiguous.append({
                    "tables": [
                        {
                            "name": t,
                            "columns": compressed.get(t, []),
                        }
                        for t in overlap
                    ],
                    "note": group["note"],
                })

        return {"ambiguous_groups": ambiguous}
