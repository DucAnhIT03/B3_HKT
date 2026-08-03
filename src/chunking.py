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
        if not text or not text.strip():
            return []

        sentences = re.split(
            r"(?<=[.!?])(?:[ \t]+|\n+)",
            text.strip(),
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        chunks: list[str] = []

        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[start : start + self.max_sentences_per_chunk]
            chunk_text = " ".join(group).strip()

            if chunk_text:
                chunks.append(chunk_text)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        separators: list[str] | None = None,
        chunk_size: int = 500,
    ) -> None:
        self.separators = (
            self.DEFAULT_SEPARATORS
            if separators is None
            else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        return self._split(text.strip(), list(self.separators))

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str],
    ) -> list[str]:
        current_text = current_text.strip()

        if not current_text:
            return []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        if separator == "":
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        if separator not in current_text:
            return self._split(current_text, next_separators)

        parts = [
            part.strip()
            for part in current_text.split(separator)
            if part.strip()
        ]

        chunks: list[str] = []
        current_chunk = ""

        for part in parts:
            candidate = (
                part
                if not current_chunk
                else current_chunk + separator + part
            )

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
                continue

            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            if len(part) > self.chunk_size:
                chunks.extend(self._split(part, next_separators))
            else:
                current_chunk = part

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same dimensions")

    dot_product = _dot(vec_a, vec_b)

    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunks = FixedSizeChunker(
            chunk_size=chunk_size,
            overlap=0,
        ).chunk(text)

        sentence_chunks = SentenceChunker(
            max_sentences_per_chunk=3,
        ).chunk(text)

        recursive_chunks = RecursiveChunker(
            chunk_size=chunk_size,
        ).chunk(text)

        strategies = {
            "fixed_size": fixed_chunks,
            "by_sentences": sentence_chunks,
            "recursive": recursive_chunks,
        }

        result = {}

        for strategy_name, chunks in strategies.items():
            count = len(chunks)

            avg_length = (
                sum(len(chunk) for chunk in chunks) / count
                if count > 0
                else 0.0
            )

            result[strategy_name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return result