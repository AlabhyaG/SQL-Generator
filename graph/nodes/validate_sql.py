from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from graph.nodes.base import BaseNode
from graph.state import GraphState


class ValidateSQLNode(BaseNode):

    def __call__(self, state: GraphState) -> dict:
        engine = create_engine(state["db_url"])
        try:
            with engine.connect() as conn:
                conn.execute(text(f"EXPLAIN {state['sql_query']}"))
            return {"sql_error": None}
        except SQLAlchemyError as e:
            error = str(e.orig) if hasattr(e, "orig") and e.orig else str(e)
            return {"sql_error": error}
        finally:
            engine.dispose()
