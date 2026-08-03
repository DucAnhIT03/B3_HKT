from __future__ import annotations

import re
from typing import Callable

from .chunking import _dot
from .store import EmbeddingStore


class SentenceRerankingStore:
    """Rerank retrieved chunks using chunk and max-sentence similarity."""

    def __init__(
        self,
        store: EmbeddingStore,
        embedding_fn: Callable[[str], list[float]],
    ) -> None:
        self.store = store
        self.embedding_fn = embedding_fn

    def get_collection_size(self) -> int:
        return self.store.get_collection_size()

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        return self.search_with_filter(query, top_k=top_k, metadata_filter=None)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        candidates = self.store.search_with_filter(
            query,
            top_k=self.store.get_collection_size(),
            metadata_filter=metadata_filter,
        )
        query_vector = self.embedding_fn(query)
        reranked: list[dict] = []
        for candidate in candidates:
            sentences = [
                sentence.strip()
                for sentence in re.split(
                    r"(?<=[.!?])\s+|\n+", candidate["content"]
                )
                if len(sentence.strip()) >= 20
            ]
            sentence_score = max(
                (
                    _dot(query_vector, self.embedding_fn(sentence))
                    for sentence in sentences
                ),
                default=float(candidate["score"]),
            )
            result = dict(candidate)
            result["base_score"] = float(candidate["score"])
            result["sentence_score"] = float(sentence_score)
            result["score"] = (
                result["base_score"] + result["sentence_score"]
            ) / 2
            reranked.append(result)
        return sorted(
            reranked,
            key=lambda item: item["score"],
            reverse=True,
        )[:top_k]
