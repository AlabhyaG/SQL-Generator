from sqlalchemy import create_engine, text

from graph.nodes.base import BaseNode
from graph.schema_analyzer import analyze_schema
from graph.schema_retriever import SchemaRetriever
from graph.state import GraphState

_SCHEMA_QUERY = """
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position
"""


class FetchSchemaNode(BaseNode):

    def __init__(self, retriever: SchemaRetriever) -> None:
        self._retriever = retriever

    def __call__(self, state: GraphState) -> dict:
        db_url = state["db_url"]

        engine = create_engine(db_url)
        try:
            with engine.connect() as conn:
                rows = conn.execute(text(_SCHEMA_QUERY)).fetchall()
        finally:
            engine.dispose()

        raw: dict[str, list[str]] = {}
        for table_name, column_name in rows:
            raw.setdefault(table_name, []).append(column_name)

        metadata = analyze_schema(raw)

        # Index in ChromaDB only if not already done for this DB
        if not self._retriever.is_indexed(db_url):
            self._retriever.index(db_url, metadata.compressed)

        full_schema = "\n".join(
            f"{table}({', '.join(cols)})"
            for table, cols in metadata.compressed.items()
        )

        return {
            "db_schema": full_schema,
            "schema_metadata": {
                "compressed": metadata.compressed,
                "groups": [
                    {
                        "name": g.name,
                        "primary": g.primary,
                        "variants": g.variants,
                        "note": g.note,
                    }
                    for g in metadata.groups
                ],
                "shared_columns": metadata.shared_columns,
                "equivalences": [
                    {"table1": e.table1, "col1": e.col1, "table2": e.table2, "col2": e.col2}
                    for e in metadata.equivalences
                ],
            },
        }
