#!/usr/bin/env python3
"""Run the frozen B3_HKT RMIT benchmark for Nguyễn Đức Anh (2A202601063)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import chunk_document, load_documents  # noqa: E402
from scripts.run_benchmark import evaluate_query, make_cached_embedder  # noqa: E402
from src.chunking import (  # noqa: E402
    FixedSizeChunker,
    HeadingSectionChunker,
    HierarchicalSectionChunker,
    RecursiveChunker,
)
from src.reranking import SentenceRerankingStore  # noqa: E402
from src.store import EmbeddingStore  # noqa: E402


QUERIES = (
    {
        "id": 1,
        "query": "How many items can undergraduate and postgraduate students borrow, for how long, and how many renewals are allowed?",
        "metadata_filter": None,
        "gold_answer": "25 items, 30 days, 1 renewal.",
        "markers": [
            "Undergraduate and postgraduate students",
            "Loan quota - 25 items",
            "Loan period - 30 days",
            "Renewals - 1",
        ],
    },
    {
        "id": 2,
        "query": "Under what conditions can a borrowed item be renewed, and how long does the renewal last?",
        "metadata_filter": None,
        "gold_answer": "The item must not be overdue or reserved by another user. Renewal lasts 15 days; the maximum total loan period is 45 days.",
        "markers": [
            "not overdue",
            "placed a reservation by another user",
            "Renewals last 15 days",
            "maximum renewal period = 45 days",
        ],
    },
    {
        "id": 3,
        "query": "What steps are required to book a Library study room?",
        "metadata_filter": None,
        "gold_answer": "Log in with an RMIT account, choose the campus, select a room and time, then confirm the booking.",
        "markers": [
            "log in with your RMIT account",
            "choose your campus",
            "select a room and time",
            "confirm your booking",
        ],
    },
    {
        "id": 4,
        "query": "What support does the Library provide to make resources accessible?",
        "metadata_filter": {"audience": "student"},
        "gold_answer": "Text digitisation, help obtaining digital resources, and converting PDF documents to text.",
        "markers": [
            "Text digitisation",
            "Helping to obtain digital resources",
            "Converting documents from PDF to text",
        ],
    },
    {
        "id": 5,
        "query": "Which reasons will the Library not accept when a user disputes a fine?",
        "metadata_filter": None,
        "gold_answer": "The ten reasons listed under Disputes are not accepted, including lack of policy knowledge, missed reminders, distance, breaks and changed hours.",
        "markers": [
            "Lack of knowledge of library polices",
            "Unwillingness to take responsibility for material loaned to a third party",
            "Forgetting the due date",
            "Not receiving library reminders",
            "Email inbox was full",
            "Unable to visit the library often or distance from the library",
            "Disagreement with the library fine policy",
            "Not being on campus",
            "Semester breaks, summer vacation",
            "Changed opening hours",
        ],
    },
)


def top1_extractive_llm(prompt: str) -> str:
    """Return the complete top-1 evidence block with its citation.

    The frozen rubric awards full credit only when one rank-1 chunk contains the
    answer. Returning that block verbatim is deterministic, fully grounded and
    makes omissions or competing facts visible instead of hiding them behind a
    generative model.
    """
    match = re.search(r"Context:\n(.*?)\n\nQuestion:", prompt, re.S)
    if not match:
        return "Không đủ thông tin trong context."
    first_block = re.split(r"(?m)(?=^\[2\])", match.group(1), maxsplit=1)[0].strip()
    if "\n" not in first_block:
        return "Không đủ thông tin trong context."
    content = first_block.split("\n", 1)[1].strip()
    return f"[1] {content}" if content else "Không đủ thông tin trong context."


def run(provider: str, data_dir: Path) -> dict:
    embedding_fn, backend_name = make_cached_embedder(provider)
    documents = load_documents(data_dir)
    configurations = {
        "recursive_300_reference": {
            "chunker": RecursiveChunker(chunk_size=300),
            "rerank": False,
            "owner": "Phan Văn Hiếu reference reproduced on the submitted corpus",
        },
        "nguyen_huy_toa_heading_400_reference": {
            "chunker": HeadingSectionChunker(chunk_size=400),
            "rerank": False,
            "owner": "Nguyễn Huy Tòa reference reproduced on the submitted corpus",
        },
        "ta_long_khanh_recursive_400": {
            "chunker": RecursiveChunker(chunk_size=400),
            "rerank": False,
            "owner": "Tạ Long Khánh — 2A202601197",
        },
        "vu_dang_huy_fixed_500_overlap_100": {
            "chunker": FixedSizeChunker(chunk_size=500, overlap=100),
            "rerank": False,
            "owner": "Vũ Đăng Huy — 2A202601761",
        },
        "hierarchical_without_rerank": {
            "chunker": HierarchicalSectionChunker(chunk_size=1600),
            "rerank": False,
            "owner": "Nguyễn Đức Anh ablation",
        },
        "nguyen_duc_anh_hierarchical_rerank": {
            "chunker": HierarchicalSectionChunker(chunk_size=1600),
            "rerank": True,
            "owner": "Nguyễn Đức Anh — 2A202601063",
        },
    }

    output = {
        "student": "Nguyễn Đức Anh",
        "student_id": "2A202601063",
        "provider": provider,
        "embedding_backend": backend_name,
        "data_dir": str(data_dir),
        "top_k": 3,
        "scoring": "2: all evidence is in rank 1 and the extractive agent includes it; 1: evidence is rank 2/3 or the top-1 answer is incomplete; 0: no complete evidence in top 3",
        "queries": list(QUERIES),
        "strategies": {},
    }

    for name, config in configurations.items():
        chunks = [
            chunk
            for document in documents
            for chunk in chunk_document(document, config["chunker"])
        ]
        base_store = EmbeddingStore(
            collection_name=f"rmit_{name}",
            embedding_fn=embedding_fn,
        )
        base_store.add_documents(chunks)
        store = (
            SentenceRerankingStore(base_store, embedding_fn)
            if config["rerank"]
            else base_store
        )

        results = []
        for query in QUERIES:
            primary = evaluate_query(
                store,
                query,
                top1_extractive_llm,
                use_filter=query["metadata_filter"] is not None,
            )
            entry = {
                "id": query["id"],
                "query": query["query"],
                "primary": primary,
            }
            if query["metadata_filter"] is not None:
                entry["unfiltered_ab"] = evaluate_query(
                    store,
                    query,
                    top1_extractive_llm,
                    use_filter=False,
                )
            results.append(entry)

        output["strategies"][name] = {
            "owner": config["owner"],
            "chunker": repr(config["chunker"].__dict__),
            "sentence_rerank": config["rerank"],
            "chunk_count": len(chunks),
            "avg_chunk_length": round(
                sum(len(chunk.content) for chunk in chunks) / len(chunks), 2
            ),
            "score": sum(item["primary"]["points"] for item in results),
            "results": results,
        }
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("local", "mock"), default="local")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "rmit-library")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "report" / "benchmark_rmit_nguyen_duc_anh.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = run(args.provider, args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Embedding backend: {output['embedding_backend']}")
    for name, stats in output["strategies"].items():
        ranks = [result["primary"]["evidence_rank"] for result in stats["results"]]
        print(
            f"{name:39} chunks={stats['chunk_count']:3} "
            f"score={stats['score']}/10 evidence_ranks={ranks}"
        )
    print(f"Saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
