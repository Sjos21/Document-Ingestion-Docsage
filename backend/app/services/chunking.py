"""Text chunking for embedding ingestion.

Word-count based approximation of token count (no tokenizer dependency
needed for the embedding model in use). ~500 "tokens" per chunk with
~50 overlap, matching architecture.md.
"""
from __future__ import annotations

from dataclasses import dataclass

CHUNK_SIZE_WORDS = 500
CHUNK_OVERLAP_WORDS = 50


@dataclass(frozen=True)
class TextChunk:
    content: str
    token_count: int  # approximate (word count)


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS,
) -> list[TextChunk]:
    """Split text into overlapping word-count-bounded chunks.

    Raises ValueError if overlap >= chunk_size (would never advance).
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    start = 0
    step = chunk_size - overlap

    while start < len(words):
        end = min(start + chunk_size, len(words))
        piece = words[start:end]
        chunks.append(TextChunk(content=" ".join(piece), token_count=len(piece)))
        if end == len(words):
            break
        start += step

    return chunks