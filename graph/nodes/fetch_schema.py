from sqlalchemy import create_engine, text

from graph.nodes.base import BaseNode
from graph.state import GraphState

_SCHEMA_QUERY = """
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position
"""


class FetchSchemaNode(BaseNode):

    def __call__(self, state: GraphState) -> dict:
        engine = create_engine(state["db_url"])
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(_SCHEMA_QUERY)).fetchall()
        finally:
            engine.dispose()

        tables: dict[str, list[str]] = {}
        for table_name, column_name, data_type in rows:
            tables.setdefault(table_name, []).append(f"{column_name} ({data_type})")

        lines = []
        for table, columns in tables.items():
            lines.append(f"Table: {table}")
            lines.extend(f"  - {col}" for col in columns)

        return {"db_schema": "\n".join(lines)}
