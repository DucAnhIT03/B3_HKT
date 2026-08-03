"""Run the five fixed CHECKPOINT 5 queries with one personal strategy.

The only experiment variable in this file is the chunker selected in
run_benchmark(). Everything else (corpus, benchmark queries, embedding
backend) remains the same between group members.
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass
from pathlib import Path

from ingest import build_knowledge_base
from main import _select_embedder, demo_llm
from src import FixedSizeChunker, KnowledgeBaseAgent


DEFAULT_DATA_DIR = "data/rmit-library"


@dataclass(frozen=True)
class BenchmarkQuery:
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
            "Log in with an RMIT account, choose the campus, "
            "select a room and time, then confirm the booking."
        ),
        expected_section=(
            "rmit-study-room-booking -> How to book a room"
        ),
    ),
    BenchmarkQuery(
        kind="List + Filter",
        query="What support does the Library provide to make resources accessible?",
        gold_answer=(
            "Text digitisation, help obtaining digital resources, "
            "and converting PDF documents to text."
        ),
        expected_section=(
            "rmit-accessibility-resources -> "
            "Resources for students with a disability"
        ),
        metadata_filter={
            "audience": "student",
        },
    ),
    BenchmarkQuery(
        kind="Exception",
        query=(
            "Which reasons will the Library not accept "
            "when a user disputes a fine?"
        ),
        gold_answer=(
            "The Library does not accept lack of policy knowledge, "
            "forgetting the due date, not receiving reminders, "
            "a full inbox, distance or inability to visit often, "
            "disagreement with the policy, being off campus, "
"semester breaks or holidays, changed opening hours, "
            "or unwillingness to take responsibility for an item "
            "loaned to a third party."
        ),
        expected_section=(
            "rmit-borrowing-returning -> Disputes -> "
            "We will not accept the following reasons"
        ),
    ),
]
def _search(store, benchmark: BenchmarkQuery) -> list[dict]:
    """Run normal search or metadata-filtered search."""
    if benchmark.metadata_filter is None:
        return store.search(benchmark.query, top_k=3)

    return store.search_with_filter(
        benchmark.query,
        top_k=3,
        metadata_filter=benchmark.metadata_filter,
    )


def run_benchmark(data_dir: str = DEFAULT_DATA_DIR) -> int:
    if not Path(data_dir).is_dir():
        print(f"Corpus directory not found: {data_dir}")
        return 1

    embedding_fn = _select_embedder()

    # ==========================================================
    # PERSONAL STRATEGY - VU DANG HUY
    # ==========================================================
    chunker = FixedSizeChunker(
        chunk_size=500,
        overlap=100,
    )

    store = build_knowledge_base(
        data_dir,
        embedding_fn=embedding_fn,
        chunker=chunker,
        collection_name="checkpoint5_vu_dang_huy",
    )

    agent = KnowledgeBaseAgent(
        store=store,
        llm_fn=demo_llm,
    )

    backend = getattr(
        embedding_fn,
        "_backend_name",
        type(embedding_fn).__name__,
    )

    print("=" * 70)
    print("CHECKPOINT 5 BENCHMARK")
    print("=" * 70)
    print(f"Corpus             : {data_dir}")
    print("Student            : Vu Dang Huy")
    print("Strategy           : FixedSizeChunker(chunk_size=500, overlap=100)")
    print(f"Embedding backend  : {backend}")
    print(f"Loaded chunks      : {store.get_collection_size()}")

    for index, benchmark in enumerate(
        BENCHMARK_QUERIES,
        start=1,
    ):
        print("\n" + "=" * 70)
        print(f"QUERY {index}/5 [{benchmark.kind}]")
        print("=" * 70)

        print(f"Query: {benchmark.query}")

        if benchmark.metadata_filter:
            print(
                "Filter:",
                json.dumps(
                    benchmark.metadata_filter,
                    ensure_ascii=False,
                ),
            )
        else:
            print("Filter: None")

        print(f"Gold Answer      : {benchmark.gold_answer}")
        print(f"Expected Section : {benchmark.expected_section}")

        results = _search(
            store,
            benchmark,
        )

        print(f"\nTop-{len(results)} Results:")

        for rank, result in enumerate(
            results,
            start=1,
        ):
            metadata = result["metadata"]

            preview = textwrap.shorten(
                " ".join(result["content"].split()),
                width=180,
                placeholder="...",
            )

            print(
                f"{rank}. "
                f"score={result['score']:.4f} | "
                f"doc_id={metadata.get('doc_id')} | "
                f"chunk={metadata.get('chunk_index')}"
            )

            print(f"   audience : {metadata.get('audience')}")
            print(f"   preview  : {preview}")

        answer = agent.answer(
            benchmark.query,
            top_k=3,
        )

        print("\nAgent Answer:")
        print(answer)

    print("\n" + "=" * 70)
    print("Benchmark completed.")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(
        run_benchmark(
            os.getenv(
                "LAB_DATA_DIR",
                DEFAULT_DATA_DIR,
            )
        )
    )
