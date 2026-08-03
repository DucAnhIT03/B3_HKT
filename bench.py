"""Run the five fixed CHECKPOINT 5 queries with one personal strategy.

The corpus, benchmark queries and embedding backend must remain the same
between group members. The personal experiment variable in this file is
the chunking strategy selected inside run_benchmark().
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ingest import build_knowledge_base
from main import _select_embedder, demo_llm
from src import RecursiveChunker


DEFAULT_DATA_DIR = "data/rmit-library"


@dataclass(frozen=True)
class BenchmarkQuery:
    """One fixed benchmark query shared by all group members."""

    kind: str
    query: str
    gold_answer: str
    expected_section: str
    metadata_filter: dict[str, str] | None = None


BENCHMARK_QUERIES = [
    BenchmarkQuery(
        kind="Number",
        query=(
            "How many items can undergraduate and postgraduate students borrow, "
            "for how long, and how many renewals are allowed?"
        ),
        gold_answer="25 items, 30 days, 1 renewal.",
        expected_section=(
            "rmit-borrowing-returning -> Student -> "
            "Undergraduate and postgraduate students"
        ),
    ),
    BenchmarkQuery(
        kind="Condition",
        query=(
            "Under what conditions can a borrowed item be renewed, "
            "and how long does the renewal last?"
        ),
        gold_answer=(
            "The item must not be overdue or reserved by another user. "
            "Renewal lasts 15 days; the maximum total loan period is 45 days."
        ),
        expected_section="rmit-borrowing-returning -> Student",
    ),
    BenchmarkQuery(
        kind="Procedure",
        query="What steps are required to book a Library study room?",
        gold_answer=(
            "Log in with an RMIT account, choose the campus, select a room "
            "and time, then confirm the booking."
        ),
        expected_section=(
            "rmit-study-room-booking -> How to book a room"
        ),
    ),
    BenchmarkQuery(
        kind="List + filter",
        query=(
            "What support does the Library provide "
            "to make resources accessible?"
        ),
        gold_answer=(
            "Text digitisation, help obtaining digital resources, "
            "and converting PDF documents to text."
        ),
        expected_section=(
            "rmit-accessibility-resources -> "
            "Resources for students with a disability"
        ),
        metadata_filter={"audience": "student"},
    ),
    BenchmarkQuery(
        kind="Exception",
        query=(
            "Which reasons will the Library not accept "
            "when a user disputes a fine?"
        ),
        gold_answer=(
            "The Library does not accept lack of policy knowledge, "
            "forgetting the due date, not receiving reminders, a full inbox, "
            "distance or inability to visit often, disagreement with the "
            "policy, being off campus, semester breaks or holidays, changed "
            "opening hours, or unwillingness to take responsibility for an "
            "item loaned to a third party."
        ),
        expected_section=(
            "rmit-borrowing-returning -> Disputes -> "
            "We will not accept the following reasons"
        ),
    ),
]


def search_benchmark(
    store: Any,
    benchmark: BenchmarkQuery,
) -> list[dict[str, Any]]:
    """Run normal search or metadata-filtered search."""

    if benchmark.metadata_filter is None:
        return store.search(
            benchmark.query,
            top_k=3,
        )

    return store.search_with_filter(
        benchmark.query,
        top_k=3,
        metadata_filter=benchmark.metadata_filter,
    )


def build_answer_from_results(
    question: str,
    results: list[dict[str, Any]],
) -> str:
    """Build a grounded prompt from the exact retrieved results.

    This helper is used instead of KnowledgeBaseAgent.answer() because the
    current agent interface does not accept metadata_filter.
    """

    if not results:
        return "No relevant information was found in the knowledge base."

    context_parts: list[str] = []

    for index, result in enumerate(results, start=1):
        metadata = result.get("metadata", {})
        doc_id = metadata.get(
            "doc_id",
            result.get("id", "unknown"),
        )
        chunk_index = metadata.get(
            "chunk_index",
            "unknown",
        )
        content = result.get("content", "")

        context_parts.append(
            f"[{index}] "
            f"doc_id={doc_id}, "
            f"chunk_index={chunk_index}\n"
            f"{content}"
        )

    context = "\n\n".join(context_parts)

    prompt = (
        "Answer the question using only the context below.\n"
        "If the context does not contain enough information, say clearly "
        "that the available context is insufficient.\n"
        "Where possible, cite the supporting context number such as [1] "
        "or [2].\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    return demo_llm(prompt)


def print_result(
    rank: int,
    result: dict[str, Any],
) -> None:
    """Print one retrieved chunk in a compact format."""

    metadata = result.get("metadata", {})
    content = result.get("content", "")
    score = float(result.get("score", 0.0))

    preview = textwrap.shorten(
        " ".join(content.split()),
        width=220,
        placeholder="...",
    )

    print(
        f"  {rank}. "
        f"score={score:.4f} "
        f"doc_id={metadata.get('doc_id')} "
        f"chunk_index={metadata.get('chunk_index')}"
    )
    print(f"     audience={metadata.get('audience')}")
    print(f"     preview={preview}")


def run_benchmark(
    data_dir: str = DEFAULT_DATA_DIR,
) -> int:
    """Load the corpus and run all five fixed benchmark queries."""

    corpus_path = Path(data_dir)

    if not corpus_path.is_dir():
        print(f"Corpus directory not found: {data_dir}")
        return 1

    embedding_fn = _select_embedder()

    # ================================================================
    # PERSONAL STRATEGY
    # Đây là biến thực nghiệm cá nhân của Tạ Long Khánh.
    # Các thành viên khác phải dùng chiến lược khác.
    # ================================================================
    chunker = RecursiveChunker(
        chunk_size=400,
    )

    store = build_knowledge_base(
        data_dir,
        embedding_fn=embedding_fn,
        chunker=chunker,
        collection_name="checkpoint5_ta_long_khanh",
    )

    backend = getattr(
        embedding_fn,
        "_backend_name",
        type(embedding_fn).__name__,
    )

    print("=" * 72)
    print("CHECKPOINT 5 BENCHMARK")
    print("=" * 72)
    print(f"Corpus: {data_dir}")
    print("Student: Ta Long Khanh")
    print("Strategy: RecursiveChunker(chunk_size=400)")
    print(f"Embedding backend: {backend}")
    print(f"Loaded chunks: {store.get_collection_size()}")
    print(f"Number of benchmark queries: {len(BENCHMARK_QUERIES)}")

    for index, benchmark in enumerate(
        BENCHMARK_QUERIES,
        start=1,
    ):
        print("\n" + "=" * 72)
        print(
            f"QUERY {index}/5 — {benchmark.kind}"
        )
        print("=" * 72)

        print(f"Query: {benchmark.query}")

        filter_text = (
            json.dumps(
                benchmark.metadata_filter,
                ensure_ascii=False,
            )
            if benchmark.metadata_filter
            else "None"
        )

        print(f"Metadata filter: {filter_text}")
        print(f"Gold answer: {benchmark.gold_answer}")
        print(f"Expected section: {benchmark.expected_section}")

        results = search_benchmark(
            store,
            benchmark,
        )

        print(f"\nTop-{len(results)} retrieved chunks:")

        if not results:
            print("  No results found.")
        else:
            for rank, result in enumerate(
                results,
                start=1,
            ):
                print_result(
                    rank,
                    result,
                )

        answer = build_answer_from_results(
            benchmark.query,
            results,
        )

        print("\nAgent answer:")
        print(answer)

    print("\n" + "=" * 72)
    print("BENCHMARK COMPLETED")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    selected_data_dir = os.getenv(
        "LAB_DATA_DIR",
        DEFAULT_DATA_DIR,
    )

    raise SystemExit(
        run_benchmark(selected_data_dir)
    )