"""Reciprocal Rank Fusion for combining ranked result lists.

RRF, not weighted score averaging: BM25 scores and cosine similarity are on
incompatible scales, so fusing by rank position (not raw score) avoids the
normalization problem entirely. Standard constant k=60 per the original
RRF paper (Cormack et al.).
"""
from __future__ import annotations

import uuid


def reciprocal_rank_fusion(
    rankings: list[list[uuid.UUID]], k: int = 60
) -> dict[uuid.UUID, float]:
    """Fuse multiple ranked ID lists into one score per ID.

    Each ranking is a list of IDs ordered best-first. An ID absent from a
    given ranking contributes 0 from that ranking (not penalized further).
    """
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores


def top_n_by_score(scores: dict[uuid.UUID, float], n: int) -> list[uuid.UUID]:
    return [
        item_id
        for item_id, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:n]
    ]