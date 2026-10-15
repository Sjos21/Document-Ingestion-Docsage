"""Cross-encoder reranking of fused candidates before LLM generation.

Small model (ms-marco-MiniLM-L-6-v2, ~80MB) to keep local-CPU rerank
latency low -- do not swap for a larger cross-encoder without re-checking
end-to-end latency budget (see architecture.md's Ollama latency notes).
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import CrossEncoder

RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL_NAME)


def rerank(query: str, candidates: list[str]) -> list[float]:
    """Return one relevance score per candidate, same order as input."""
    if not candidates:
        return []
    model = _get_reranker()
    pairs = [(query, c) for c in candidates]
    scores = model.predict(pairs)
    return [float(s) for s in scores]