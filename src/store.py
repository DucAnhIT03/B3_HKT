from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            self._client = chromadb.EphemeralClient()
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)

        record = {
            "id": str(doc.id),
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        results: list[dict[str, Any]] = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])

            results.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": score,
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)

        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            ids: list[str] = []
            documents: list[str] = []
            embeddings: list[list[float]] = []
            metadatas: list[dict[str, Any]] = []

            for record in records:
                unique_id = f"{record['id']}-{self._next_index}"
                self._next_index += 1

                ids.append(unique_id)
                documents.append(record["content"])
                embeddings.append(record["embedding"])
                metadatas.append(record["metadata"])

            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            for record in records:
                self._store.append(record)
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            collection_size = self._collection.count()

            if collection_size == 0:
                return []

            query_embedding = self._embedding_fn(query)

            response = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection_size),
                include=["documents", "metadatas", "distances"],
            )

            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]

            results: list[dict[str, Any]] = []

            for record_id, content, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
            ):
                results.append(
                    {
                        "id": record_id,
                        "content": content,
                        "metadata": metadata or {},
                        "score": 1.0 - float(distance),
                    }
                )

            results.sort(key=lambda item: item["score"], reverse=True)
            return results

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()

        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            collection_size = self._collection.count()

            if collection_size == 0:
                return []

            query_embedding = self._embedding_fn(query)

            response = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection_size),
                where=metadata_filter,
                include=["documents", "metadatas", "distances"],
            )

            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]

            results: list[dict[str, Any]] = []

            for record_id, content, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
            ):
                results.append(
                    {
                        "id": record_id,
                        "content": content,
                        "metadata": metadata or {},
                        "score": 1.0 - float(distance),
                    }
                )

            results.sort(key=lambda item: item["score"], reverse=True)
            return results[:top_k]

        filtered_records = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )
        ]

        return self._search_records(
            query=query,
            records=filtered_records,
            top_k=top_k,
        )

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            existing = self._collection.get(
                where={"doc_id": doc_id},
                include=["metadatas"],
            )

            existing_ids = existing.get("ids", [])

            if not existing_ids:
                return False

            self._collection.delete(ids=existing_ids)
            return True

        size_before = len(self._store)

        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]

        return len(self._store) < size_before
