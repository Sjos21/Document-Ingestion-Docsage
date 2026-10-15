import uuid

from app.services.fusion import reciprocal_rank_fusion, top_n_by_score


def test_rrf_favors_item_ranked_high_in_both_lists() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    vector_ranking = [a, b, c]
    bm25_ranking = [a, c, b]

    scores = reciprocal_rank_fusion([vector_ranking, bm25_ranking])

    assert scores[a] > scores[b]
    assert scores[a] > scores[c]


def test_rrf_item_only_in_one_list_still_scored() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    scores = reciprocal_rank_fusion([[a], []])
    assert a in scores
    assert b not in scores


def test_top_n_by_score_orders_descending() -> None:
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    scores = {a: 0.1, b: 0.9, c: 0.5}
    assert top_n_by_score(scores, 2) == [b, c]