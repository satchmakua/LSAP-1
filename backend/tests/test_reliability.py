import numpy as np

from lsap.coordinates.reliability import (
    _pearson,
    correlation_matrix,
    forced_choice_agreement,
    redundant_pairs,
    run_pca,
    scalar_axis_agreement,
    twin_consistency,
)


def test_scalar_agreement_identical_and_monotonic_offset():
    a = np.array([1, 2, 3, 4, 5, 6, 7])
    same = scalar_axis_agreement(a, a)
    assert same["within1_rate"] == 1.0
    assert same["mean_abs_diff"] == 0.0
    assert same["spearman"] == 1.0

    off = scalar_axis_agreement(a, a + 1)  # shifted by 1 everywhere
    assert off["within1_rate"] == 1.0
    assert off["mean_abs_diff"] == 1.0
    assert off["spearman"] == 1.0  # still perfectly monotonic


def test_scalar_agreement_reversed_is_anticorrelated():
    a = np.array([1, 2, 3, 4, 5, 6, 7])
    m = scalar_axis_agreement(a, a[::-1])
    assert m["spearman"] == -1.0
    assert m["mean_abs_diff"] > 2


def test_forced_choice_agreement():
    a = np.array([1, 2, 3, 1, 2])
    assert forced_choice_agreement(a, a)["exact_match_rate"] == 1.0
    assert forced_choice_agreement(a, np.array([2, 3, 1, 2, 3]))["exact_match_rate"] == 0.0


def test_correlation_flags_a_redundant_pair():
    # columns A and B are identical; C differs.
    m = np.array([[1, 1, 3], [2, 2, 1], [3, 3, 4], [4, 4, 2], [5, 5, 5]], float)
    corr = correlation_matrix(m)
    pairs = redundant_pairs(corr, ["A", "B", "C"], threshold=0.8)
    assert pairs, "expected at least one redundant pair"
    assert {pairs[0][0], pairs[0][1]} == {"A", "B"}
    assert abs(pairs[0][2] - 1.0) < 1e-9


def test_pca_concentrates_on_one_dominant_factor():
    latent = np.arange(1, 11, dtype=float)
    m = np.stack([latent * 2, latent * 0.5 + 1, -latent], axis=1)  # all collinear
    out = run_pca(m, ["A", "B", "C"])
    assert out["explained_variance_ratio"][0] > 0.99
    assert out["n_for_90pct"] == 1
    assert len(out["top_axes_per_component"][0]) == 3  # only 3 axes


def test_twin_consistency_zero_for_identical_twins():
    seg_ids = ["s1", "s2", "t1", "t2"]
    m = np.array([[1, 2, 3], [5, 5, 5], [2, 2, 2], [2, 2, 2]], float)  # t1 == t2
    out = twin_consistency(m, seg_ids, {"s1": None, "s2": None, "t1": "p1", "t2": "p1"})
    assert out["n_twin_pairs"] == 1
    assert out["mean_twin_distance"] == 0.0
    assert out["mean_all_pairs_distance"] > 0


def test_pearson_constant_column_is_zero_not_nan():
    assert _pearson(np.array([1, 1, 1]), np.array([1, 2, 3])) == 0.0
