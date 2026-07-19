import numpy as np
from fastapi.testclient import TestClient

from lsap import storage
from lsap.api.app import app
from lsap.coordinates.projection import ProjectionModel
from lsap.instrument.schema import AxisScore, Rating

client = TestClient(app)

AXES = ["A", "B"]
NAMES = {"A": "Axis A", "B": "Axis B"}
MATRIX = np.array([[1, 7], [2, 5], [6, 3], [7, 1]], dtype=float)
SEGS = [{"id": f"s{i}", "profile": "prof", "pair": None} for i in range(4)]


def _fit_and_save(tmp_path):
    m = ProjectionModel.fit(MATRIX, AXES, NAMES, SEGS)
    m.save(tmp_path / "coordinates" / "model.json")
    return m


def _rate(seg_id: str, a: int, b: int) -> None:
    storage.save_rating(
        Rating(
            segment_id=seg_id,
            rater_id="m1",
            flagged=False,
            created_at="2026-07-03T00:00:00Z",
            scores=[
                AxisScore(axis_id="A", value=a, confidence=5),
                AxisScore(axis_id="B", value=b, confidence=5),
            ],
        )
    )


def test_cspace_is_409_without_a_fitted_projection(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    r = client.get("/api/cspace")
    assert r.status_code == 409
    assert "fit_projection" in r.json()["detail"]


def test_cspace_returns_factors_and_normalized_points(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    m = _fit_and_save(tmp_path)
    body = client.get("/api/cspace").json()
    assert body["n_segments"] == 4
    assert len(body["points"]) == 4
    assert len(body["factors"]) == len(m.factors)
    # labels are derived from real axis names; variance is real; residual is acknowledged
    assert "Axis" in body["factors"][0]["label"]
    assert body["factors"][0]["explained_variance"] > 0
    assert 0.0 <= body["residual"] < 1.0
    assert all(0.0 <= c <= 1.0 for p in body["points"] for c in p["coords"])


def test_segment_projection_returns_vector_and_neighbors(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    m = _fit_and_save(tmp_path)
    _rate("s0", 1, 7)  # same values as fitted row 0

    body = client.get("/api/segments/s0/projection?k=2").json()
    assert body["segment_id"] == "s0"
    assert len(body["vector"]["coords"]) == len(m.factors)
    assert body["vector"]["residual"] == m.residual
    assert len(body["neighbors"]) == 2
    ids = [n["segment_id"] for n in body["neighbors"]]
    assert "s0" not in ids  # never its own neighbour
    # nearest neighbour of row 0 is the adjacent row, not the far end of the axis
    assert ids[0] == "s1"


def test_segment_projection_404_when_unrated(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    _fit_and_save(tmp_path)
    assert client.get("/api/segments/never-rated/projection").status_code == 404
