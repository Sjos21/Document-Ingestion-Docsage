"""Deterministic IR metrics. relevant_id = the one correct chunk/doc id per query."""
from __future__ import annotations


def recall_at_k(ranked_ids: list, relevant_id, k: int) -> float:
    return 1.0 if relevant_id in ranked_ids[:k] else 0.0


def precision_at_k(ranked_ids: list, relevant_ids: set, k: int) -> float:
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    return sum(1 for i in top_k if i in relevant_ids) / len(top_k)


def reciprocal_rank(ranked_ids: list, relevant_id) -> float:
    for i, rid in enumerate(ranked_ids, start=1):
        if rid == relevant_id:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked_ids: list, relevant_id, k: int) -> float:
    import math
    top_k = ranked_ids[:k]
    dcg = sum(1.0 / math.log2(i + 1) for i, rid in enumerate(top_k, start=1) if rid == relevant_id)
    idcg = 1.0  # single relevant item, best case rank 1 -> 1/log2(2)=1
    return dcg / idcg if idcg else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0