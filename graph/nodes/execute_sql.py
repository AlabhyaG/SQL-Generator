from sqlalchemy import create_engine, text

from graph.nodes.base import BaseNode
from graph.state import GraphState


class ExecuteSQLNode(BaseNode):

    def __call__(self, state: GraphState) -> dict:
        engine = create_engine(state["db_url"])
        try:
            with engine.connect() as conn:
                result = conn.execute(text(state["sql_query"]))
                rows = [dict(row._mapping) for row in result.fetchall()]
            return {"raw_results": rows}
        finally:
            engine.dispose()
