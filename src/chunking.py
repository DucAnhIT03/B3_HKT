from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]
        limit = self.max_sentences_per_chunk
        return [
            " ".join(sentences[index : index + limit])
            for index in range(0, len(sentences), limit)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        chunks = self._split(text, self.separators)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        chunk_size = max(1, self.chunk_size)
        if len(current_text) <= chunk_size:
            return [current_text]

        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[index : index + chunk_size]
                for index in range(0, len(current_text), chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        if separator not in current_text:
            return self._split(current_text, next_separators)

        parts = [part.strip() for part in current_text.split(separator) if part.strip()]
        if not parts:
            return self._split(current_text, next_separators)

        chunks: list[str] = []
        current_chunk = ""
        for part in parts:
            candidate = part if not current_chunk else current_chunk + separator + part
            if len(candidate) <= chunk_size:
                current_chunk = candidate
                continue

            if current_chunk:
                chunks.append(current_chunk)

            if len(part) > chunk_size:
                chunks.extend(self._split(part, next_separators))
                current_chunk = ""
            else:
                current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)
        return chunks


class HeadingAwareChunker:
    """Split Markdown by heading, then recursively split oversized sections.

    The section heading is repeated on every child chunk so retrieved fragments
    keep their local context even after a long section has been divided.
    """

    HEADING_PATTERN = r"^#{1,6}\s+"

    def __init__(self, max_chunk_size: int = 400) -> None:
        self.max_chunk_size = max(1, max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        sections = re.split(
            rf"(?={self.HEADING_PATTERN})",
            text.strip(),
            flags=re.MULTILINE,
        )
        chunks: list[str] = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.splitlines()
            has_heading = bool(re.match(self.HEADING_PATTERN, lines[0]))
            heading = lines[0].strip() if has_heading else ""
            body = "\n".join(lines[1:]).strip() if has_heading else section

            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue

            prefix = f"{heading}\n" if heading else ""
            body_chunk_size = max(1, self.max_chunk_size - len(prefix))
            recursive = RecursiveChunker(chunk_size=body_chunk_size)

            for child in recursive.chunk(body):
                chunk = f"{prefix}{child}".strip()
                if chunk:
                    chunks.append(chunk)

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            comparison[name] = {
                "count": count,
                "avg_length": sum(len(chunk) for chunk in chunks) / count if count else 0.0,
                "chunks": chunks,
            }
        return comparison
