"""Run the frozen five-query benchmark with Huy Toan's chunking strategy."""

from __future__ import annotations

import sys
from typing import Any

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import HeadingAwareChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder

DATA_DIR = "data/rmit-library"
TOP_K = 3
STRATEGY_NAME = "HeadingAwareChunker(max_chunk_size=400)"

# Frozen group benchmark: do not change queries, corpus, gold answers, or filters
# after any member has started evaluating a strategy.
BENCHMARKS: list[dict[str, Any]] = [
    {
        "kind": "numeric",
        "query": (
            "How many items can undergraduate and postgraduate students borrow, "
            "for how long, and how many renewals are allowed?"
        ),
        "metadata_filter": None,
    },
    {
        "kind": "condition",
        "query": (
            "Under what conditions can a borrowed item be renewed, and how long "
            "does the renewal last?"
        ),
        "metadata_filter": None,
    },
    {
        "kind": "process",
        "query": "What steps are required to book a Library study room?",
        "metadata_filter": None,
    },
    {
        "kind": "list + metadata filter",
        "query": "What support does the Library provide to make resources accessible?",
        "metadata_filter": {"audience": "student"},
    },
    {
        "kind": "exception",
        "query": "Which reasons will the Library not accept when a user disputes a fine?",
        "metadata_filter": None,
    },
]


class _FilteredStoreView:
    """Expose a filtered ``search`` method to KnowledgeBaseAgent."""

    def __init__(self, store, metadata_filter: dict[str, str]) -> None:
        self.store = store
        self.metadata_filter = metadata_filter

    def search(self, query: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
        return self.store.search_with_filter(
            query,
            top_k=top_k,
            metadata_filter=self.metadata_filter,
        )


def _configure_console_encoding() -> None:
    """Print Unicode consistently in PowerShell and cmd on Windows."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _extractive_llm(prompt: str) -> str:
    """Return the top retrieved passage as a deterministic CP5 agent answer.

    CP5 checks that the complete benchmark pipeline runs and prints an answer.
    Retrieval quality and answer synthesis are evaluated separately in CP6.
    """
    context_marker = "Context:\n"
    question_marker = "\n\nQuestion:"
    context = prompt.partition(context_marker)[2].partition(question_marker)[0].strip()
    first_chunk = context.split("\n\n[2]", maxsplit=1)[0]
    lines = first_chunk.splitlines()
    answer = "\n".join(lines[1:]).strip() if len(lines) > 1 else first_chunk
    if len(answer) > 600:
        return answer[:597].rstrip() + "..."
    return answer or "No extractive answer was available."


def _preview(content: str, limit: int = 180) -> str:
    compact = " ".join(content.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def run_benchmark() -> int:
    _configure_console_encoding()

    print("=== CHECKPOINT 5 BENCHMARK ===")
    print(f"Corpus: {DATA_DIR}")
    print(f"Strategy: {STRATEGY_NAME}")
    print(f"Embedding model: {LOCAL_EMBEDDING_MODEL}")

    embedder = LocalEmbedder(model_name=LOCAL_EMBEDDING_MODEL)

    # This is the only strategy-specific selection in the benchmark pipeline.
    chunker = HeadingAwareChunker(max_chunk_size=400)
    store = build_knowledge_base(DATA_DIR, embedder, chunker=chunker)
    print(f"Loaded chunks: {store.get_collection_size()}")

    for index, benchmark in enumerate(BENCHMARKS, start=1):
        query = benchmark["query"]
        metadata_filter = benchmark["metadata_filter"]

        print(f"\n--- Query {index}: {benchmark['kind']} ---")
        print(f"Question: {query}")
        print(f"Metadata filter: {metadata_filter or 'none'}")

        if metadata_filter:
            results = store.search_with_filter(
                query,
                top_k=TOP_K,
                metadata_filter=metadata_filter,
            )
            agent_store = _FilteredStoreView(store, metadata_filter)
        else:
            results = store.search(query, top_k=TOP_K)
            agent_store = store

        print("Top 3:")
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            print(
                f"  {rank}. score={result['score']:.4f} "
                f"doc_id={metadata.get('doc_id', 'unknown')} "
                f"chunk_index={metadata.get('chunk_index', 'unknown')}"
            )
            print(f"     preview={_preview(result['content'])}")

        agent = KnowledgeBaseAgent(store=agent_store, llm_fn=_extractive_llm)
        print(f"Agent answer (extractive CP5): {agent.answer(query, top_k=TOP_K)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_benchmark())
