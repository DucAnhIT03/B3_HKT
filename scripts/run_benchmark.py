#!/usr/bin/env python3
"""Run the fixed K3 retrieval benchmark at chunk level.

The output records top-k evidence, marker hits, an extractive grounded answer,
and A/B metadata-filter results for each built-in chunking strategy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import chunk_document, load_documents  # noqa: E402
from src.agent import KnowledgeBaseAgent  # noqa: E402
from src.chunking import (  # noqa: E402
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    _dot,
)
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder, _mock_embed  # noqa: E402
from src.store import EmbeddingStore  # noqa: E402


QUERIES = [
    {
        "id": 1,
        "query": "Sinh viên năm nhất nhận được những hình thức hỗ trợ nào từ First-Year Librarians?",
        "metadata_filter": {"audience": "student"},
        "gold_answer": (
            "First-Year Librarians là đầu mối thư viện cá nhân, cung cấp hướng dẫn, "
            "tư vấn và giới thiệu dịch vụ phù hợp."
        ),
        "markers": ["guidance, consultations and referrals"],
    },
    {
        "id": 2,
        "query": "Người dùng được mượn tối đa bao nhiêu sách trên Libby cùng lúc, giữ trong bao lâu và đặt trước bao nhiêu sách?",
        "metadata_filter": None,
        "gold_answer": "Tối đa 3 sách cùng lúc, 14 ngày mỗi lượt và tối đa 5 lượt đặt trước.",
        "markers": [
            "A Libby loan lasts 14 days",
            "no more than three books at once",
            "up to five books on hold",
        ],
    },
    {
        "id": 3,
        "query": "Tài liệu mượn thông thường được tự động gia hạn tối đa bao nhiêu lần, với điều kiện gì?",
        "metadata_filter": None,
        "gold_answer": "Tối đa 5 lần nếu không có người dùng khác yêu cầu tài liệu.",
        "markers": [
            "If no other user requests a regular loan item, its loan period is automatically renewed up to five times"
        ],
    },
    {
        "id": 4,
        "query": "Giảng viên phải làm gì để đặt một buổi hướng dẫn thư viện cho lớp và nên gửi yêu cầu khi nào?",
        "metadata_filter": {"audience": "faculty"},
        "gold_answer": "Liên hệ library liaison hoặc gửi request, và gửi càng sớm càng tốt.",
        "markers": [
            "contacting their library liaison or submitting a request",
            "Requests should be submitted as early as possible",
        ],
    },
    {
        "id": 5,
        "query": "BorrowDirect cho mượn loại tài liệu nào, trong bao lâu và có được gia hạn không?",
        "metadata_filter": None,
        "gold_answer": "Sách in và bản nhạc; thời hạn 16 tuần và không được gia hạn.",
        "markers": ["printed books and music scores", "loan lasts 16 weeks and cannot be renewed"],
    },
]


class StaticResultStore:
    """Minimal store adapter so the agent uses one already-scored result set."""

    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def search(self, _question: str, top_k: int = 3) -> list[dict]:
        return self.results[:top_k]


def make_cached_embedder(provider: str) -> tuple[Callable[[str], list[float]], str]:
    backend = _mock_embed if provider == "mock" else LocalEmbedder(LOCAL_EMBEDDING_MODEL)

    @lru_cache(maxsize=None)
    def cached(text: str) -> tuple[float, ...]:
        return tuple(float(value) for value in backend(text))

    def embed(text: str) -> list[float]:
        return list(cached(text))

    return embed, getattr(backend, "_backend_name", backend.__class__.__name__)


def make_extractive_llm(embedding_fn: Callable[[str], list[float]]) -> Callable[[str], str]:
    """Select the four context sentences most similar to the question."""

    def answer(prompt: str) -> str:
        context_match = re.search(r"Context:\n(.*?)\n\nQuestion:", prompt, re.S)
        question_match = re.search(r"Question:\s*(.*?)\nAnswer:", prompt, re.S)
        if not context_match or not question_match:
            return "Không đủ thông tin trong context."

        question = question_match.group(1).strip()
        candidates: list[tuple[str, str]] = []
        blocks = re.split(r"(?m)(?=^\[\d+\])", context_match.group(1))
        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 2 or not lines[0].startswith("["):
                continue
            citation = lines[0].split("]", 1)[0] + "]"
            content = "\n".join(lines[1:])
            sentences = re.split(r"(?<=[.!?])\s+|\n+", content)
            candidates.extend(
                (citation, sentence.strip())
                for sentence in sentences
                if len(sentence.strip()) >= 20
            )

        if not candidates:
            return "Không đủ thông tin trong context."

        query_vector = embedding_fn(question)
        ranked = sorted(
            candidates,
            key=lambda item: _dot(query_vector, embedding_fn(item[1])),
            reverse=True,
        )
        selected: list[str] = []
        seen: set[str] = set()
        for citation, sentence in ranked:
            normalized = sentence.casefold()
            if normalized in seen:
                continue
            selected.append(f"{citation} {sentence}")
            seen.add(normalized)
            if len(selected) == 4:
                break
        return " ".join(selected)

    return answer


def marker_rank(results: list[dict], markers: list[str]) -> int | None:
    ranks: list[int] = []
    for marker in markers:
        matching_rank = next(
            (
                rank
                for rank, result in enumerate(results, start=1)
                if marker.casefold() in result["content"].casefold()
            ),
            None,
        )
        if matching_rank is None:
            return None
        ranks.append(matching_rank)
    return max(ranks)


def serialize_result(result: dict, markers: list[str]) -> dict:
    content = result["content"]
    return {
        "id": result["id"],
        "doc_id": result["metadata"].get("doc_id"),
        "chunk_index": result["metadata"].get("chunk_index"),
        "score": round(float(result["score"]), 6),
        "marker_hits": [marker for marker in markers if marker.casefold() in content.casefold()],
        "content": content,
    }


def evaluate_query(
    store: EmbeddingStore,
    query_spec: dict,
    extractive_llm: Callable[[str], str],
    use_filter: bool,
) -> dict:
    metadata_filter = query_spec["metadata_filter"] if use_filter else None
    results = store.search_with_filter(
        query_spec["query"],
        top_k=3,
        metadata_filter=metadata_filter,
    )
    evidence_rank = marker_rank(results, query_spec["markers"])
    agent = KnowledgeBaseAgent(StaticResultStore(results), extractive_llm)
    agent_answer = agent.answer(query_spec["query"], top_k=3)
    agent_correct = all(
        marker.casefold() in agent_answer.casefold()
        for marker in query_spec["markers"]
    )
    points = 0
    if evidence_rank is not None:
        points = 2 if evidence_rank == 1 and agent_correct else 1
    return {
        "metadata_filter": metadata_filter,
        "top3": [serialize_result(result, query_spec["markers"]) for result in results],
        "evidence_rank": evidence_rank,
        "agent_answer": agent_answer,
        "agent_correct": agent_correct,
        "points": points,
    }


def run(provider: str, data_dir: Path) -> dict:
    embedding_fn, backend_name = make_cached_embedder(provider)
    extractive_llm = make_extractive_llm(embedding_fn)
    strategies = {
        "fixed_size": FixedSizeChunker(chunk_size=500, overlap=50),
        "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
        "recursive": RecursiveChunker(chunk_size=500),
    }
    documents = load_documents(data_dir)
    output = {
        "provider": provider,
        "embedding_backend": backend_name,
        "data_dir": str(data_dir),
        "top_k": 3,
        "scoring": "2 if all markers are in rank-1 evidence and extractive answer; 1 if evidence is rank 2/3 or answer omits a marker; otherwise 0",
        "queries": QUERIES,
        "strategies": {},
    }

    for strategy_name, chunker in strategies.items():
        chunks = [chunk for doc in documents for chunk in chunk_document(doc, chunker)]
        store = EmbeddingStore(
            collection_name=f"benchmark_{strategy_name}",
            embedding_fn=embedding_fn,
        )
        store.add_documents(chunks)
        query_results: list[dict] = []
        for query_spec in QUERIES:
            primary = evaluate_query(
                store,
                query_spec,
                extractive_llm,
                use_filter=query_spec["metadata_filter"] is not None,
            )
            entry = {
                "id": query_spec["id"],
                "query": query_spec["query"],
                "markers": query_spec["markers"],
                "primary": primary,
            }
            if query_spec["metadata_filter"] is not None:
                entry["unfiltered_ab"] = evaluate_query(
                    store,
                    query_spec,
                    extractive_llm,
                    use_filter=False,
                )
            query_results.append(entry)

        output["strategies"][strategy_name] = {
            "chunk_count": len(chunks),
            "avg_chunk_length": round(
                sum(len(chunk.content) for chunk in chunks) / len(chunks),
                2,
            ) if chunks else 0.0,
            "score": sum(entry["primary"]["points"] for entry in query_results),
            "results": query_results,
        }
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("local", "mock"), default="local")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "k3_university")
    parser.add_argument("--output", type=Path, default=ROOT / "report" / "benchmark_results.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run(args.provider, args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Embedding backend: {results['embedding_backend']}")
    for name, stats in results["strategies"].items():
        print(
            f"{name:13} chunks={stats['chunk_count']:2} "
            f"avg={stats['avg_chunk_length']:6.2f} score={stats['score']}/10"
        )
    print(f"Saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
