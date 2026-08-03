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
        "evidence": [
            "Undergraduate and postgraduate students",
            "Loan quota - 25 items",
            "Loan period - 30 days",
            "Renewals - 1",
        ],
        "metadata_filter": None,
    },
    {
        "kind": "condition",
        "query": (
            "Under what conditions can a borrowed item be renewed, and how long "
            "does the renewal last?"
        ),
        "evidence": [
            "not overdue",
            "reservation by another user",
            "Renewals last 15 days",
        ],
        "metadata_filter": None,
    },
    {
        "kind": "process",
        "query": "What steps are required to book a Library study room?",
        "evidence": [
            "log in with your RMIT account",
            "choose your campus",
            "confirm your booking",
        ],
        "metadata_filter": None,
    },
    {
        "kind": "list + metadata filter",
        "query": "What support does the Library provide to make resources accessible?",
        "evidence": [
            "Text digitisation",
            "Helping to obtain digital resources",
            "Converting documents from PDF to text",
        ],
        "metadata_filter": {"audience": "student"},
    },
    {
        "kind": "exception",
        "query": "Which reasons will the Library not accept when a user disputes a fine?",
        "evidence": [
            "Lack of knowledge of library polices",
            "Forgetting the due date",
            "Changed opening hours",
        ],
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


def _matching_evidence(content: str, evidence: list[str]) -> list[str]:
    """Return the expected evidence phrases actually present in one chunk."""
    normalized_content = content.casefold()
    return [
        phrase
        for phrase in evidence
        if phrase.casefold() in normalized_content
    ]


def run_benchmark() -> int:
    _configure_console_encoding()

    print("=== CHECKPOINT 6 BENCHMARK ANALYSIS ===")
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
        evidence = benchmark["evidence"]
        metadata_filter = benchmark["metadata_filter"]

        print(f"\n--- Query {index}: {benchmark['kind']} ---")
        print(f"Question: {query}")
        print(f"Metadata filter: {metadata_filter or 'none'}")
        print(f"Required evidence: {evidence}")

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
        retrieved_evidence: set[str] = set()
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            matches = _matching_evidence(result["content"], evidence)
            retrieved_evidence.update(matches)
            if len(matches) == len(evidence):
                relevance = "FULL EVIDENCE"
            elif matches:
                relevance = "PARTIAL EVIDENCE"
            else:
                relevance = "NO EVIDENCE"
            print(
                f"  {rank}. score={result['score']:.4f} "
                f"doc_id={metadata.get('doc_id', 'unknown')} "
                f"chunk_index={metadata.get('chunk_index', 'unknown')} "
                f"relevance={relevance}"
            )
            print(f"     evidence_hits={matches or 'none'}")
            print(f"     preview={_preview(result['content'])}")

        missing_evidence = [
            phrase for phrase in evidence if phrase not in retrieved_evidence
        ]
        print(
            f"Evidence coverage in top-3: "
            f"{len(retrieved_evidence)}/{len(evidence)}"
        )
        print(f"Missing evidence: {missing_evidence or 'none'}")

        agent = KnowledgeBaseAgent(store=agent_store, llm_fn=_extractive_llm)
        print(f"Agent answer (extractive): {agent.answer(query, top_k=TOP_K)}")

        if metadata_filter:
            print("\nA/B FILTER COMPARISON")
            print("A = without metadata filter")
            unfiltered_results = store.search(query, top_k=TOP_K)
            unfiltered_evidence: set[str] = set()

            for rank, result in enumerate(unfiltered_results, start=1):
                metadata = result["metadata"]
                matches = _matching_evidence(result["content"], evidence)
                unfiltered_evidence.update(matches)
                if len(matches) == len(evidence):
                    relevance = "FULL EVIDENCE"
                elif matches:
                    relevance = "PARTIAL EVIDENCE"
                else:
                    relevance = "NO EVIDENCE"
                print(
                    f"  {rank}. score={result['score']:.4f} "
                    f"doc_id={metadata.get('doc_id', 'unknown')} "
                    f"chunk_index={metadata.get('chunk_index', 'unknown')} "
                    f"audience={metadata.get('audience', 'unknown')} "
                    f"relevance={relevance}"
                )
                print(f"     evidence_hits={matches or 'none'}")
                print(f"     preview={_preview(result['content'])}")

            filtered_ranking = [
                (
                    result["metadata"].get("doc_id"),
                    result["metadata"].get("chunk_index"),
                )
                for result in results
            ]
            unfiltered_ranking = [
                (
                    result["metadata"].get("doc_id"),
                    result["metadata"].get("chunk_index"),
                )
                for result in unfiltered_results
            ]
            print("B = with metadata filter")
            print(f"  filter={metadata_filter}")
            print(f"  ranking={filtered_ranking}")
            print(
                f"  evidence_coverage="
                f"{len(retrieved_evidence)}/{len(evidence)}"
            )
            print(f"A ranking={unfiltered_ranking}")
            print(
                f"A evidence_coverage="
                f"{len(unfiltered_evidence)}/{len(evidence)}"
            )
            print(f"Top-3 changed by filter: {unfiltered_ranking != filtered_ranking}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_benchmark())
