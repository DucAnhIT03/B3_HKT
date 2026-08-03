"""CHECKPOINT 6: compare strategies using answer-bearing chunk evidence."""

from __future__ import annotations

from dataclasses import dataclass

from bench import (
    BENCHMARK_QUERIES,
    HeadingRecursiveChunker,
    evidence_rank,
    select_benchmark_embedder,
)
from ingest import build_knowledge_base
from src import FixedSizeChunker, RecursiveChunker, SentenceChunker


DATA_DIR = "data/rmit-library"


@dataclass
class StrategyResult:
    name: str
    chunk_count: int
    evidence_ranks: list[int | None]
    filter_rank: int | None
    no_filter_rank: int | None

    @property
    def top3_hits(self) -> int:
        return sum(rank is not None for rank in self.evidence_ranks)

    @property
    def points(self) -> int:
        return sum(
            2 if rank == 1 else 1 if rank in (2, 3) else 0
            for rank in self.evidence_ranks
        )


def _retrieve(store, benchmark, *, apply_filter: bool = True) -> list[dict]:
    if apply_filter and benchmark.metadata_filter:
        return store.search_with_filter(
            benchmark.query,
            top_k=3,
            metadata_filter=benchmark.metadata_filter,
        )
    return store.search(benchmark.query, top_k=3)


def evaluate_strategy(name: str, chunker, embedding_fn) -> StrategyResult:
    store = build_knowledge_base(
        DATA_DIR,
        embedding_fn=embedding_fn,
        chunker=chunker,
        collection_name=f"cp6_{name}",
    )
    ranks = [
        evidence_rank(_retrieve(store, benchmark), benchmark)
        for benchmark in BENCHMARK_QUERIES
    ]

    filtered_query = next(
        benchmark for benchmark in BENCHMARK_QUERIES if benchmark.metadata_filter
    )
    filter_rank = evidence_rank(_retrieve(store, filtered_query), filtered_query)
    no_filter_rank = evidence_rank(
        _retrieve(store, filtered_query, apply_filter=False),
        filtered_query,
    )
    return StrategyResult(
        name=name,
        chunk_count=store.get_collection_size(),
        evidence_ranks=ranks,
        filter_rank=filter_rank,
        no_filter_rank=no_filter_rank,
    )


def main() -> int:
    embedding_fn = select_benchmark_embedder()
    backend = getattr(embedding_fn, "_backend_name", type(embedding_fn).__name__)
    strategies = {
        "fixed_400_overlap_40": FixedSizeChunker(chunk_size=400, overlap=40),
        "sentence_3": SentenceChunker(max_sentences_per_chunk=3),
        "recursive_400": RecursiveChunker(chunk_size=400),
        "heading_recursive_400": HeadingRecursiveChunker(chunk_size=400),
        "recursive_300_personal": RecursiveChunker(chunk_size=300),
    }

    print("=== CHECKPOINT 6 STRATEGY COMPARISON ===")
    print(f"Embedding backend: {backend}")
    print("Scoring: 2=answer-bearing chunk at top-1, 1=at top-2/3, 0=absent")
    print()
    print("strategy | chunks | Q1 Q2 Q3 Q4 Q5 | top3 hits | points/10")
    print("-" * 83)

    results = []
    for name, chunker in strategies.items():
        result = evaluate_strategy(name, chunker, embedding_fn)
        results.append(result)
        rank_cells = " ".join(str(rank or "-") for rank in result.evidence_ranks)
        print(
            f"{name:28} | {result.chunk_count:6} | {rank_cells:14} | "
            f"{result.top3_hits}/5       | {result.points}/10"
        )

    print("\nA/B FILTER — Query 4")
    print("strategy | no filter evidence rank | student filter evidence rank")
    print("-" * 72)
    for result in results:
        print(
            f"{result.name:28} | {str(result.no_filter_rank or '-'):23} | "
            f"{result.filter_rank or '-'}"
        )

    personal = next(r for r in results if r.name == "recursive_300_personal")
    failures = [
        index
        for index, rank in enumerate(personal.evidence_ranks, start=1)
        if rank != 1
    ]
    print("\nPersonal strategy failure candidates:", failures or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
