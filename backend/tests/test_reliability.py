import numpy as np

from lsap import storage
from lsap.coordinates.reliability import (
    _pearson,
    compare_reports,
    correlation_matrix,
    forced_choice_agreement,
    format_comparison,
    load_rater_matrices,
    origin_structure_comparison,
    redundant_pairs,
    run_pca,
    scalar_axis_agreement,
    split_half_stability,
    twin_consistency,
)
from lsap.instrument.schema import AxisDef, AxisScore, Rating


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


def _two_factor_matrix(n: int, seed: int = 7) -> np.ndarray:
    """8 axes driven by 2 independent latents plus small noise — a real structure."""
    rng = np.random.default_rng(seed)
    f1, f2 = rng.normal(size=n), rng.normal(size=n)
    cols = [f1 * w for w in (2.0, 1.5, -1.8, 1.2)] + [f2 * w for w in (2.0, -1.6, 1.4, 1.1)]
    return np.stack(cols, axis=1) + rng.normal(scale=0.15, size=(n, 8))


def test_split_half_stability_high_for_structure_low_for_noise():
    stable = split_half_stability(_two_factor_matrix(60), n_components=2, seed=1)
    assert stable["mean_abs_r"] > 0.9
    noise = np.random.default_rng(3).normal(size=(60, 8))
    unstable = split_half_stability(noise, n_components=2, seed=1)
    assert unstable["mean_abs_r"] < stable["mean_abs_r"] - 0.2


def test_split_half_stability_is_deterministic_and_guards_small_n():
    m = _two_factor_matrix(40)
    a = split_half_stability(m, seed=5)
    b = split_half_stability(m, seed=5)
    assert a == b  # seeded — no wall-clock randomness
    assert "error" in split_half_stability(m[:6])


def test_origin_comparison_matches_when_minority_shares_the_structure():
    m = _two_factor_matrix(50)
    origins = ["model"] * 40 + ["public-domain"] * 10
    out = origin_structure_comparison(m, origins, [f"A{i}" for i in range(8)], n_components=2)
    assert out is not None
    assert out["majority_origin"] == "model"
    assert out["n_minority"] == 10
    # Both halves are draws from the same generator, so the loadings must match well.
    assert min(out["loading_match_abs_r"]) > 0.8
    assert len(out["top_axis_offsets"]) == 5


def test_origin_comparison_none_without_a_real_minority():
    m = _two_factor_matrix(30)
    assert origin_structure_comparison(m, ["model"] * 30, [f"A{i}" for i in range(8)]) is None
    origins = ["model"] * 27 + ["public-domain"] * 3  # below the n>=5 floor
    assert origin_structure_comparison(m, origins, [f"A{i}" for i in range(8)]) is None


# ---- storage-backed selection (the M5 defect fix) -----------------------------------

TWO_AXES = [
    AxisDef(id="L1", field="L", name="Lexical Complexity", kind="scalar",
            definition="d", anchors={1: "a", 4: "b", 7: "c"}),
    AxisDef(id="L3", field="L", name="Semantic Density", kind="scalar",
            definition="d", anchors={1: "a", 4: "b", 7: "c"}),
]


def _save(seg: str, rater: str, values: tuple[int, int], *, axes_version: int = 1) -> None:
    storage.save_rating(
        Rating(
            segment_id=seg, rater_id=rater, axes_version=axes_version,
            scores=[
                AxisScore(axis_id="L1", value=values[0], confidence=5),
                AxisScore(axis_id="L3", value=values[1], confidence=5),
            ],
            flagged=False, created_at="2026-07-19T00:00:00Z",
        )
    )


def _pilot(seg: str) -> None:
    storage.save_segment(seg, "some text", source="pilot", created_at="t")


def test_load_rater_matrices_uses_the_newer_appended_rating(tmp_path, monkeypatch):
    """The M5 defect: first-wins silently ignored every re-rate. Newest must win."""
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    for seg in ("p1", "p2"):
        _pilot(seg)
        _save(seg, "claude-opus-4-8", (4, 4))
        _save(seg, "claude-haiku-4-5", (5, 5))
    _save("p1", "claude-opus-4-8", (2, 6))  # the re-rate

    seg_ids, values, _conf, _meta = load_rater_matrices(TWO_AXES, axes_version=1)
    assert seg_ids == ["p1", "p2"]
    opus = values["claude-opus-4-8"]
    assert opus[0].tolist() == [2, 6]  # newer rating, not the first one
    assert opus[1].tolist() == [4, 4]


def test_load_rater_matrices_selects_one_axes_version_cohort(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    for seg in ("p1", "p2"):
        _pilot(seg)
        _save(seg, "claude-opus-4-8", (4, 4), axes_version=1)
    _save("p1", "claude-opus-4-8", (7, 7), axes_version=2)

    _ids, v1, _c1, _m1 = load_rater_matrices(TWO_AXES, axes_version=1)
    assert v1["claude-opus-4-8"][0].tolist() == [4, 4]  # v2 never pollutes the v1 cohort
    _ids, v2, _c2, _m2 = load_rater_matrices(TWO_AXES, axes_version=2)
    assert v2["claude-opus-4-8"][0].tolist() == [7, 7]
    assert np.isnan(v2["claude-opus-4-8"][1]).all()  # p2 unrated under v2 stays NaN


def test_load_rater_matrices_restricts_to_only_segments(tmp_path, monkeypatch):
    """The like-for-like guard: comparing cohorts must not mix in segments only one
    cohort has, or corpus growth would masquerade as an anchor effect."""
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    for seg in ("old1", "old2", "new1"):
        _pilot(seg)
        _save(seg, "claude-opus-4-8", (4, 4), axes_version=2)
    _save("old1", "claude-opus-4-8", (1, 1), axes_version=1)
    _save("old2", "claude-opus-4-8", (1, 1), axes_version=1)

    common = {"old1", "old2"}
    seg_ids, values, _c, _m = load_rater_matrices(
        TWO_AXES, axes_version=2, only_segments=common
    )
    assert seg_ids == ["old1", "old2"]  # new1 excluded even though it has v2 ratings
    assert values["claude-opus-4-8"].shape[0] == 2


def test_compare_reports_flags_regressions_and_labels_versions():
    def _rep(version: int, l1: float, n1: float) -> dict:
        return {
            "axes_version": version,
            "axis_agreement": {
                "L1": {"name": "Lexical Complexity", "kind": "scalar", "within1_rate": l1},
                "N1": {"name": "Event Density", "kind": "scalar", "within1_rate": n1},
            },
        }

    cmp = compare_reports(_rep(1, 0.40, 0.90), _rep(2, 0.73, 0.70))
    assert cmp["axes"]["L1"]["delta"] == 0.33
    assert cmp["regressions"] == ["N1"]  # 0.90 -> 0.70 is a > 0.10 drop
    text = format_comparison(cmp)
    assert "axes_version 1 vs 2" in text
    assert "regressions (> 0.10 drop): N1" in text
