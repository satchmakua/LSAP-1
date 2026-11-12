import numpy as np
import pytest

from lsap import storage
from lsap.coordinates.projection import (
    CVector,
    ProjectionModel,
    consensus_for_segment,
    consensus_panel,
    fit_from_storage,
)
from lsap.instrument.schema import AxisDef, AxisScore, Rating

AXES = ["L1", "L2", "N1", "C3"]
NAMES = {"L1": "Lexical Complexity", "L2": "Syntactic Depth", "N1": "Event Density",
         "C3": "Cognitive Transparency"}

# Two clear clusters: rows 0-2 "compressed/exterior", rows 3-5 "expansive/interior".
MATRIX = np.array(
    [
        [2, 2, 6, 2],
        [2, 3, 6, 2],
        [1, 2, 7, 1],
        [6, 7, 2, 7],
        [6, 6, 2, 6],
        [7, 7, 1, 7],
    ],
    dtype=float,
)
SEGMENTS = [
    {"id": "a1", "profile": "min", "pair": "p"},
    {"id": "a2", "profile": "min", "pair": None},
    {"id": "a3", "profile": "min", "pair": None},
    {"id": "b1", "profile": "max", "pair": "p"},
    {"id": "b2", "profile": "max", "pair": None},
    {"id": "b3", "profile": "max", "pair": None},
]


def _fit() -> ProjectionModel:
    return ProjectionModel.fit(MATRIX, AXES, NAMES, SEGMENTS)


def test_fit_produces_factors_points_and_residual():
    m = _fit()
    assert len(m.factors) >= 1
    assert len(m.points) == 6
    # every fitted point is normalized into [0,1] on each factor
    for p in m.points:
        assert all(0.0 <= c <= 1.0 for c in p["coords"])
    # a dominant first factor is expected for two clean clusters
    assert m.explained_variance()[0] > 0.5
    assert 0.0 <= m.residual < 1.0
    # degenerate (~0 variance) components are dropped, not kept as noise dimensions
    assert all(f["explained_variance"] > 0 for f in m.factors)
    # labels are derived from real axis names, not invented
    assert any(NAMES[a] in m.factors[0]["label"] for a in AXES)


def test_project_matches_the_fitted_point():
    m = _fit()
    v = m.project(dict(zip(AXES, MATRIX[0], strict=True)))
    assert isinstance(v, CVector)
    assert v.coords == pytest.approx(m.points[0]["coords"], abs=1e-3)
    assert v.residual == m.residual


def test_project_rejects_missing_axes():
    m = _fit()
    with pytest.raises(ValueError):
        m.project({"L1": 3.0})


def test_neighbors_finds_the_same_cluster_and_excludes_self():
    m = _fit()
    a1 = next(p for p in m.points if p["segment_id"] == "a1")
    nb = m.neighbors(a1["scores"], k=3, exclude="a1")
    assert "a1" not in [n.segment_id for n in nb]
    # nearest neighbours of a "min" segment should be the other "min" segments
    assert {nb[0].segment_id, nb[1].segment_id} <= {"a2", "a3"}
    assert nb[0].distance <= nb[1].distance <= nb[2].distance


def test_save_load_round_trip(tmp_path):
    m = _fit()
    p = m.save(tmp_path / "coordinates" / "model.json")
    assert p.exists()
    loaded = ProjectionModel.load(p)
    assert loaded is not None
    assert loaded.axis_ids == m.axis_ids
    assert loaded.explained_variance() == m.explained_variance()
    v1 = m.project(dict(zip(AXES, MATRIX[3], strict=True)))
    v2 = loaded.project(dict(zip(AXES, MATRIX[3], strict=True)))
    assert v1.coords == pytest.approx(v2.coords)


def test_load_returns_none_when_absent(tmp_path):
    assert ProjectionModel.load(tmp_path / "nope.json") is None


def test_fit_requires_two_segments():
    with pytest.raises(ValueError):
        ProjectionModel.fit(MATRIX[:1], AXES, NAMES, SEGMENTS[:1])


# ---- consensus selection (the M5 defect fix) ----------------------------------------


def _save(seg: str, rater: str, value: int, *, axes_version: int = 1) -> None:
    storage.save_rating(
        Rating(
            segment_id=seg, rater_id=rater, axes_version=axes_version,
            scores=[AxisScore(axis_id="L1", value=value, confidence=5)],
            flagged=False, created_at="2026-07-19T00:00:00Z",
        )
    )


def test_consensus_uses_the_newer_appended_rating(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    _save("s", "claude-opus-4-8", 4)
    _save("s", "claude-haiku-4-5", 6)
    _save("s", "claude-opus-4-8", 2)  # the re-rate; first-wins would average 4 and 6
    assert consensus_for_segment("s", ["L1"]) == {"L1": 4.0}  # mean(2, 6)


def test_consensus_never_pools_axes_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    _save("s", "claude-opus-4-8", 4, axes_version=1)
    _save("s", "claude-haiku-4-5", 6, axes_version=1)
    _save("s", "claude-opus-4-8", 1, axes_version=2)
    # Default: the newest cohort only — not 1 averaged with a stale v1 haiku 6.
    assert consensus_for_segment("s", ["L1"]) == {"L1": 1.0}
    # Explicit cohorts stay separately addressable.
    assert consensus_for_segment("s", ["L1"], axes_version=1) == {"L1": 5.0}
    assert consensus_for_segment("s", ["L1"], axes_version=3) is None


# ---- the consensus panel ------------------------------------------------------------


def test_consensus_panel_admits_only_raters_with_near_full_coverage():
    assert consensus_panel({"opus": 1.0, "haiku": 0.95, "human:sh": 0.08}) == ["haiku", "opus"]
    # nobody qualifies (e.g. midway through a re-rate) -> every rater, as before
    assert consensus_panel({"opus": 0.5, "haiku": 0.4}) == ["haiku", "opus"]
    assert consensus_panel({}) == []


def test_consensus_ignores_raters_outside_the_panel(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    _save("s", "claude-opus-4-8", 2)
    _save("s", "claude-haiku-4-5", 4)
    _save("s", "human:sh", 7)
    panel = ["claude-haiku-4-5", "claude-opus-4-8"]
    assert consensus_for_segment("s", ["L1"], raters=panel) == {"L1": 3.0}  # not 4.33
    # a segment no panel member has rated falls back to whoever did rate it
    _save("only-human", "human:sh", 6)
    assert consensus_for_segment("only-human", ["L1"], raters=panel) == {"L1": 6.0}


TWO_SCALAR = [
    AxisDef(id="L1", field="L", name="Lexical Complexity", kind="scalar",
            definition="d", anchors={1: "a", 4: "b", 7: "c"}),
    AxisDef(id="L2", field="L", name="Syntactic Depth", kind="scalar",
            definition="d", anchors={1: "a", 4: "b", 7: "c"}),
]


def _save2(seg: str, rater: str, l1: int, l2: int) -> None:
    storage.save_rating(
        Rating(
            segment_id=seg, rater_id=rater, axes_version=1,
            scores=[AxisScore(axis_id="L1", value=l1, confidence=5),
                    AxisScore(axis_id="L2", value=l2, confidence=5)],
            flagged=False, created_at="2026-07-19T00:00:00Z",
        )
    )


def test_fit_is_unmoved_by_a_partial_coverage_rater(tmp_path, monkeypatch):
    """A rater who has scored 2 of 10 segments must not shift where those 2 land: the
    fitted frame comes from one rater panel, and the panel is recorded in the model."""
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    for i in range(10):
        storage.save_segment(f"s{i}", "text", source="pilot", created_at="t")
        _save2(f"s{i}", "claude-opus-4-8", 1 + i % 7, 1 + (i * 3) % 7)
        _save2(f"s{i}", "claude-haiku-4-5", 1 + (i + 1) % 7, 1 + (i * 3 + 1) % 7)
    before = fit_from_storage(TWO_SCALAR, axes_version=1)
    assert before.d["raters"] == ["claude-haiku-4-5", "claude-opus-4-8"]

    _save2("s0", "human:sh", 7, 7)
    _save2("s1", "human:sh", 7, 7)
    partial = fit_from_storage(TWO_SCALAR, axes_version=1)
    assert partial.d["raters"] == before.d["raters"]
    assert partial.d["mean"] == before.d["mean"]
    assert partial.points == before.points

    for i in range(2, 10):  # once the third rater covers everything, it joins the panel
        _save2(f"s{i}", "human:sh", 7, 7)
    full = fit_from_storage(TWO_SCALAR, axes_version=1)
    assert full.d["raters"] == ["claude-haiku-4-5", "claude-opus-4-8", "human:sh"]
    assert full.d["mean"] != before.d["mean"]


# ---- twin ranks ---------------------------------------------------------------------


def test_twin_ranks_report_where_each_twin_lands():
    matrix = MATRIX.copy()
    matrix[1] = matrix[0]  # a1 and a2 are identical -> each is the other's nearest
    segments = [dict(s) for s in SEGMENTS]
    for s in segments:
        s["pair"] = None
    segments[0]["pair"] = segments[1]["pair"] = "close"  # a1, a2
    segments[2]["pair"] = segments[5]["pair"] = "far"    # a3 (min) vs b3 (max)
    m = ProjectionModel.fit(matrix, AXES, NAMES, segments)

    ranks = {r["segment_id"]: r for r in m.twin_ranks()}
    assert set(ranks) == {"a1", "a2", "a3", "b3"}
    assert ranks["a1"]["twin"] == "a2" and ranks["a1"]["rank"] == 1
    assert ranks["a2"]["rank"] == 1
    # opposite clusters: the twin is among the farthest of the 5 other segments
    assert ranks["a3"]["rank"] >= 3 and ranks["b3"]["rank"] >= 3


def test_twin_ranks_empty_without_pairs():
    segments = [{**s, "pair": None} for s in SEGMENTS]
    assert ProjectionModel.fit(MATRIX, AXES, NAMES, segments).twin_ranks() == []
