#!/usr/bin/env python3
"""Measure the five sentence pairs reported in REPORT_CANHAN.md."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.chunking import compute_similarity  # noqa: E402
from src.embeddings import LocalEmbedder  # noqa: E402


PAIRS = [
    (
        "Undergraduate and postgraduate students can borrow 25 items for 30 days.",
        "Sinh viên đại học và sau đại học được mượn 25 tài liệu trong 30 ngày.",
    ),
    (
        "Undergraduate and postgraduate students can borrow 25 items for 30 days.",
        "Dự báo ngày mai trời có mưa lớn.",
    ),
    (
        "The Library provides text digitisation and converts PDF documents to text.",
        "Thư viện số hóa văn bản và chuyển tài liệu PDF sang dạng văn bản.",
    ),
    (
        "Items can be renewed if they are not overdue.",
        "Overdue items can be renewed.",
    ),
    (
        "Undergraduate students may borrow 25 items.",
        "Alumni may borrow 5 items.",
    ),
]


def main() -> int:
    embedder = LocalEmbedder()
    for index, (sentence_a, sentence_b) in enumerate(PAIRS, start=1):
        score = compute_similarity(embedder(sentence_a), embedder(sentence_b))
        print(f"{index}: {score:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
