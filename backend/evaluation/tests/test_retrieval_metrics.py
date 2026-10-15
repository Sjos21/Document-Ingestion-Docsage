from evaluation.metrics.retrieval_metrics import mean, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def test_recall_at_k_hit_and_miss():
    assert recall_at_k(["a", "b", "c"], "b", 2) == 1.0
    assert recall_at_k(["a", "b", "c"], "z", 2) == 0.0


def test_precision_at_k():
    assert precision_at_k(["a", "b", "c"], {"a", "c"}, 3) == 2 / 3


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], "b") == 0.5
    assert reciprocal_rank(["a", "b", "c"], "z") == 0.0


def test_ndcg_prefers_higher_rank():
    assert ndcg_at_k(["x", "a"], "a", 2) < ndcg_at_k(["a", "x"], "a", 2)


def test_mean():
    assert mean([1.0, 0.0, 1.0]) == pytest_approx(2 / 3)


def pytest_approx(v, tol=1e-6):
    class _A:
        def __eq__(self, other):
            return abs(other - v) < tol
    return _A()