"""Embedding generation via sentence-transformers (local, CPU-only)."""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL_VERSION = EMBEDDING_MODEL_NAME  # stored on each chunk row
EMBEDDING_DIM = 384


@lru_cache
def _get_model() -> SentenceTransformer:
    """Load once per process; sentence-transformers handles thread-safety
    for encode() calls on a shared model instance."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embed a list of chunk texts. Returns one 384-dim vector per input."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, batch_size=32, show_progress_bar=False)
    return [v.tolist() for v in vectors]