import numpy as np

from lsap import storage
from lsap.coordinates.reliability import (
    _average_ranks,
    _pearson,
    _spearman,
    build_report,
    compare_reports,
    correlation_matrix,
    forced_choice_agreement,
    format_comparison,
    format_report,
    human_model_divergence,
    load_rater_matrices,
    origin_generalization,
    redundant_pairs,
    run_pca,
    scalar_axis_agreement,
    split_half_stability,
    twin_consistency,
)
from lsap.instrument.schema import AxisDef, AxisScore, Rating, load_axes


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


def test_average_ranks_share_ties():
    assert _average_ranks(np.array([10, 20, 10, 30])).tolist() == [1.5, 3.0, 1.5, 4.0]
    assert _average_ranks(np.array([5, 5, 5])).tolist() == [2.0, 2.0, 2.0]


def test_spearman_is_not_fooled_by_the_order_of_tied_values():
    """Ordinal 1–7 scores are mostly ties. Ranking by position (argsort of argsort) gave
    these two raters rho = +0.6; with ties sharing a rank they are exactly uncorrelated."""
    a = np.array([1, 1, 2, 2])
    b = np.array([1, 2, 1, 2])
    assert _spearman(a, b) == 0.0
    # and it is invariant to the order the segments happen to be listed in
    perm = np.array([3, 0, 2, 1])
    assert _spearman(a[perm], b[perm]) == 0.0


AXIS8 = [f"A{i}" for i in range(8)]


def test_origin_generalization_no_gap_when_minority_shares_the_structure():
    m = _two_factor_matrix(100)
    origins = ["model"] * 85 + ["public-domain"] * 15
    out = origin_generalization(m, origins, AXIS8, n_components=2, n_splits=60)
    assert out is not None
    assert out["majority_origin"] == "model"
    assert (out["n_majority"], out["n_minority"]) == (85, 15)
    # Both groups are draws from the same generator: the factors describe them equally.
    assert abs(out["gap"]) < 0.05
    assert out["captured_minority"]["mean"] > 0.9
    assert len(out["top_axis_offsets"]) == 5


def test_origin_generalization_detects_variance_the_factors_do_not_describe():
    """The check must be able to fail. Here the minority varies along a direction the
    majority never uses, so factors fitted on the majority capture far less of it."""
    rng = np.random.default_rng(11)
    shared = np.array([2.0, 1.5, -1.8, 1.2, 2.0, -1.6, 1.4, 1.1])  # the one real factor
    unused = np.array([1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0])  # majority never moves here

    def draw(n: int, off_factor: float) -> np.ndarray:
        on = rng.normal(size=(n, 1)) * shared
        off = rng.normal(size=(n, 1)) * off_factor * unused
        return on + off + rng.normal(scale=0.15, size=(n, 8))

    rows = np.vstack([draw(85, off_factor=0.0), draw(15, off_factor=2.0)])
    origins = ["model"] * 85 + ["public-domain"] * 15
    out = origin_generalization(rows, origins, AXIS8, n_components=1, n_splits=60)
    assert out is not None
    assert out["captured_holdout_majority"]["mean"] > 0.9  # the factor fits its own kind
    assert out["gap"] > 0.15
    assert out["minority_lower_in_share_of_splits"] > 0.9


def test_origin_generalization_is_deterministic_and_needs_a_real_minority():
    m = _two_factor_matrix(60)
    origins = ["model"] * 50 + ["public-domain"] * 10
    a = origin_generalization(m, origins, AXIS8, n_components=2, n_splits=20, seed=3)
    b = origin_generalization(m, origins, AXIS8, n_components=2, n_splits=20, seed=3)
    assert a == b  # seeded — no wall-clock randomness
    assert origin_generalization(m, ["model"] * 60, AXIS8) is None
    few = ["model"] * 57 + ["public-domain"] * 3  # below the n>=5 floor
    assert origin_generalization(m, few, AXIS8) is None


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


def _save_full(seg: str, rater_id: str, *, base: int, axes_version: int = 1) -> None:
    """A full 30-axis rating (real axis ids) so build_report runs end to end. Values
    alternate by segment and axis so no column is constant (a zero-variance column has no
    correlation), while every rater keeps the same fixed offset from `base`."""
    axes = load_axes()
    n = int(seg.lstrip("s"))
    storage.save_rating(
        Rating(
            segment_id=seg, rater_id=rater_id, axes_version=axes_version,
            scores=[
                AxisScore(axis_id=a.id, value=base + (n + k) % 2, confidence=4)
                for k, a in enumerate(axes)
            ],
            flagged=False, created_at="2026-07-19T00:00:00Z",
        )
    )


def test_build_report_three_raters_with_ragged_human_coverage(tmp_path, monkeypatch):
    """M7: a third (human) rater covering only part of the corpus yields three pairwise
    columns, pairwise-complete — that rater is never silently dropped or densely padded."""
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    axes = load_axes()
    for i in range(10):
        s = f"s{i}"
        _pilot(s)
        _save_full(s, "claude-opus-4-8", base=4)
        _save_full(s, "claude-haiku-4-5", base=5)
    for i in range(4):  # the human rater scores only 4 of the 10 (ragged coverage)
        _save_full(f"s{i}", "human:sh", base=6)

    report = build_report(axes, axes_version=1)
    assert len(report["rater_pairs"]) == 3  # 3 choose 2

    pairs = report["axis_agreement"]["L1"]["pairs"]
    assert len(pairs) == 3
    human_pairs = {k: v for k, v in pairs.items() if "human:sh" in k}
    assert len(human_pairs) == 2
    for pm in human_pairs.values():
        assert pm["n"] == 4  # pairwise-complete: only the segments both rated
    model_pair = next(v for k, v in pairs.items() if "human" not in k)
    assert model_pair["n"] == 10  # the model↔model pair still spans the whole corpus

    # The headline is weighted by each pair's n. Within-1 here is 1.0 for opus↔haiku
    # (n=10) and haiku↔human (n=4), 0.0 for opus↔human (n=4): 14/18, not the flat 2/3
    # that would let a pair sharing 4 segments count as much as one sharing 10.
    assert report["axis_agreement"]["L1"]["within1_rate"] == round(14 / 18, 4)

    # A rater covering 4 of 10 segments is compared against the consensus, never pooled
    # into it — otherwise those 4 segments' consensus would differ in kind from the rest.
    assert report["consensus_raters"] == ["claude-haiku-4-5", "claude-opus-4-8"]
    assert report["n_segments_in_pca"] == 10

    hmd = report["human_model_divergence"]
    assert hmd is not None and len(hmd) == 2  # human vs each of the two models
    # every listed axis carries the pairwise-complete n and an agreement score
    some = next(iter(hmd.values()))
    assert some and all("agreement" in r and r["n"] == 4 for r in some)

    text = format_report(report)
    assert "Human" in text and "human:sh" in text


def test_build_report_only_raters_drops_the_others(tmp_path, monkeypatch):
    """Comparing two anchor cohorts must hold the rater set fixed as well as the segments."""
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    axes = load_axes()
    for i in range(4):
        s = f"s{i}"
        _pilot(s)
        _save_full(s, "claude-opus-4-8", base=4)
        _save_full(s, "claude-haiku-4-5", base=5)
        _save_full(s, "human:sh", base=6)

    both = build_report(
        axes, axes_version=1, only_raters={"claude-opus-4-8", "claude-haiku-4-5"}
    )
    assert both["raters"] == ["claude-haiku-4-5", "claude-opus-4-8"]
    assert len(both["rater_pairs"]) == 1
    assert both["human_model_divergence"] is None
    # with full coverage a third rater does join the panel
    assert build_report(axes, axes_version=1)["consensus_raters"] == [
        "claude-haiku-4-5", "claude-opus-4-8", "human:sh",
    ]


def test_human_model_divergence_none_without_a_human():
    agree = {"L1": {"name": "Lexical Complexity", "kind": "scalar",
                    "pairs": {"claude-opus-4-8 vs claude-haiku-4-5":
                              {"within1_rate": 0.5, "n": 10}}}}
    assert human_model_divergence(agree, ["claude-opus-4-8", "claude-haiku-4-5"]) is None


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
