#!/usr/bin/env python3
"""Validate the K3 corpus and its one-to-one source registry."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import load_documents  # noqa: E402


DATA_DIR = ROOT / "data" / "k3_university"
REQUIRED_METADATA = {
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
    "department",
    "category",
    "language",
}


def main() -> int:
    documents = load_documents(DATA_DIR)
    with (DATA_DIR / "sources.csv").open(encoding="utf-8", newline="") as source_file:
        sources = list(csv.DictReader(source_file))

    assert 5 <= len(documents) <= 10, "corpus must contain 5-10 documents"
    assert len(documents) == len(sources), "sources.csv must have one row per document"
    assert len({document.id for document in documents}) == len(documents), "duplicate doc_id"
    assert {document.id for document in documents} == {row["doc_id"] for row in sources}

    for document in documents:
        missing = REQUIRED_METADATA - document.metadata.keys()
        assert not missing, f"{document.id}: missing metadata {sorted(missing)}"
        assert str(document.metadata["source_url"]).startswith("https://")
        assert document.metadata["audience"] in {"student", "faculty", "staff", "all"}
        assert len(str(document.metadata["retrieved_at"])) == 10
        print(
            f"{document.id}: body_chars={len(document.content)}, "
            f"audience={document.metadata['audience']}, "
            f"category={document.metadata['category']}"
        )

    for row in sources:
        source_path = ROOT / row["file_path"]
        assert source_path.is_file(), f"missing source file: {source_path}"
        assert row["license_or_permission"], f"{row['doc_id']}: permission is empty"

    print(f"corpus_validation: OK ({len(documents)} documents, {len(sources)} source rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
