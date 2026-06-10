import hashlib

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

VECTORSTORE_PATH = "vectorstore"


class SchemaRetriever:
    """
    Wraps ChromaDB. One collection per database (keyed by db_url hash).
    Embeddings are persisted to disk under VECTORSTORE_PATH.
    """

    def __init__(self, path: str = VECTORSTORE_PATH) -> None:
        self._client = chromadb.PersistentClient(path=path)
        self._ef = DefaultEmbeddingFunction()

    # ── Public ────────────────────────────────────────────────────────────────

    def index(self, db_url: str, compressed: dict[str, list[str]]) -> None:
        """Embed and store each table. Upsert so re-runs are safe."""
        collection = self._collection(db_url)
        ids, documents = [], []
        for table, cols in compressed.items():
            ids.append(table)
            documents.append(f"{table}: {', '.join(cols)}")
        if ids:
            collection.upsert(ids=ids, documents=documents)

    def retrieve(self, db_url: str, question: str, k: int = 5) -> list[str]:
        """Return top-k table names most relevant to the question."""
        try:
            collection = self._collection(db_url)
            total = collection.count()
            if total == 0:
                return []
            results = collection.query(
                query_texts=[question],
                n_results=min(k, total),
            )
            return results["ids"][0]
        except Exception:
            return []

    def is_indexed(self, db_url: str) -> bool:
        try:
            return self._collection(db_url).count() > 0
        except Exception:
            return False

    # ── Private ───────────────────────────────────────────────────────────────

    def _collection(self, db_url: str):
        key = hashlib.md5(db_url.encode()).hexdigest()[:16]
        return self._client.get_or_create_collection(
            name=f"schema_{key}",
            embedding_function=self._ef,
        )
