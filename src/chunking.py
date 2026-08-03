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
        return [
            " ".join(sentences[index : index + self.max_sentences_per_chunk])
            for index in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = list(self.DEFAULT_SEPARATORS) if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        return [
            piece.strip()
            for piece in self._split(text, self.separators)
            if piece.strip()
        ]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        if separator not in current_text:
            return self._split(current_text, next_separators)

        raw_parts = current_text.split(separator)
        parts = [
            part + (separator if index < len(raw_parts) - 1 else "")
            for index, part in enumerate(raw_parts)
        ]

        chunks: list[str] = []
        current_chunk = ""
        for part in parts:
            if not part:
                continue

            if len(part) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(self._split(part, next_separators))
                continue

            if current_chunk and len(current_chunk) + len(part) > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = part
            else:
                current_chunk += part

        if current_chunk:
            chunks.append(current_chunk)
        return chunks


class HeadingSectionChunker:
    """Split Markdown by headings and retain the H1 title on every section.

    This K3-specific strategy keeps a section semantically complete while the
    repeated document title gives independently retrieved H2 chunks their
    parent topic. Oversized sections fall back to ``RecursiveChunker``.
    """

    HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        matches = list(self.HEADING_RE.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        document_title = next(
            (match.group(2).strip() for match in matches if len(match.group(1)) == 1),
            "",
        )
        chunks: list[str] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            section = text[match.start() : end].strip()
            prefix = ""
            if document_title and len(match.group(1)) > 1:
                prefix = f"# {document_title}\n\n"

            available_size = max(1, self.chunk_size - len(prefix))
            pieces = RecursiveChunker(chunk_size=available_size).chunk(section)
            chunks.extend(
                f"{prefix}{piece}".strip()
                for piece in pieces
                if piece.strip()
            )
        return chunks


class HeadingWindowChunker:
    """Create bounded windows from Markdown H2 sections.

    The K3 corpus contains multi-condition answers split across neighboring
    sections (for example, loan rules followed by eligible material). Documents
    with at most ``sections_per_chunk`` sections keep them together; documents
    with more sections keep one focused section per chunk. H2 headings stay in
    the embedded text; provenance remains available through chunk metadata.
    """

    HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")

    def __init__(self, sections_per_chunk: int = 2, chunk_size: int = 1200) -> None:
        self.sections_per_chunk = max(1, sections_per_chunk)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        matches = list(self.HEADING_RE.finditer(text))
        h2_matches = [match for match in matches if len(match.group(1)) == 2]
        if not h2_matches:
            return HeadingSectionChunker(chunk_size=self.chunk_size).chunk(text)

        sections: list[str] = []
        for match in h2_matches:
            next_heading = next(
                (candidate for candidate in matches if candidate.start() > match.start()),
                None,
            )
            end = next_heading.start() if next_heading else len(text)
            sections.append(text[match.start() : end].strip())

        windows = (
            [sections]
            if len(sections) <= self.sections_per_chunk
            else [[section] for section in sections]
        )

        chunks: list[str] = []
        for window in windows:
            window_text = "\n\n".join(window)
            combined = window_text.strip()
            chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(combined))
        return chunks


class HierarchicalSectionChunker:
    """Keep a Markdown heading together with its complete semantic subtree.

    A compact subtree (for example ``Undergraduate and postgraduate students``
    or ``Disputes``) becomes one independently retrievable chunk. Large parent
    sections are represented by their child subtrees instead of duplicating a
    very broad chunk. A short whole document is retained because some RMIT
    pages express one answer as several adjacent heading-only feature cards.

    This strategy avoids crossing sibling heading boundaries, which prevents a
    quota for one audience from being mixed with another audience. It also
    keeps a heading and a long list together when the subtree fits the limit.
    """

    HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")

    def __init__(self, chunk_size: int = 1600) -> None:
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        matches = list(self.HEADING_RE.finditer(text))
        if not matches:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        chunks: list[str] = []
        for index, match in enumerate(matches):
            level = len(match.group(1))
            end = next(
                (
                    candidate.start()
                    for candidate in matches[index + 1 :]
                    if len(candidate.group(1)) <= level
                ),
                len(text),
            )
            subtree = text[match.start() : end].strip()
            heading_only = f"{match.group(1)} {match.group(2)}".strip()
            if subtree == heading_only:
                continue
            if len(subtree) <= self.chunk_size:
                chunks.append(subtree)
                continue

            next_heading = matches[index + 1] if index + 1 < len(matches) else None
            if next_heading is None or next_heading.start() >= end:
                chunks.extend(
                    RecursiveChunker(chunk_size=self.chunk_size).chunk(subtree)
                )
                continue

            # Preserve any prose directly below a broad parent heading. Child
            # subtrees are emitted by their own iterations and carry the detail.
            parent_intro = text[match.start() : next_heading.start()].strip()
            if parent_intro != heading_only:
                chunks.extend(
                    RecursiveChunker(chunk_size=self.chunk_size).chunk(parent_intro)
                )

        # Nested headings can occasionally yield byte-for-byte identical
        # chunks. Stable de-duplication prevents them occupying multiple top-k
        # slots without changing source order.
        return list(dict.fromkeys(chunk for chunk in chunks if chunk.strip()))


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
        safe_chunk_size = max(1, chunk_size)
        fixed_overlap = min(50, safe_chunk_size - 1)
        strategy_chunks = {
            "fixed_size": FixedSizeChunker(
                chunk_size=safe_chunk_size,
                overlap=fixed_overlap,
            ).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=safe_chunk_size).chunk(text),
        }

        result: dict = {}
        for name, chunks in strategy_chunks.items():
            count = len(chunks)
            result[name] = {
                "count": count,
                "avg_length": sum(len(chunk) for chunk in chunks) / count if count else 0.0,
                "chunks": chunks,
            }
        return result
