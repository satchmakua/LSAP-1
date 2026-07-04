from fastapi.testclient import TestClient

from lsap.api import app as app_module
from lsap.api.app import app
from lsap.instrument.rater import RaterError
from lsap.instrument.schema import AxisScore, Rating

client = TestClient(app)


def _fake_rating(seg_id: str, rater_id: str) -> Rating:
    scores = [AxisScore(axis_id=f"X{i}", value=4, confidence=5) for i in range(30)]
    return Rating(
        segment_id=seg_id, rater_id=rater_id, scores=scores, flagged=False,
        created_at="2026-07-03T00:00:00Z",
    )


def test_rate_endpoint_persists_and_reads_back(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))

    def fake_rate(*, segment_id, segment_text, rater, axes, created_at, client=None):
        assert len(axes) == 30
        return _fake_rating(segment_id, rater)

    monkeypatch.setattr(app_module.rater, "rate", fake_rate)

    r = client.post("/api/rate", json={"text": "some prose here", "title": "My Scene"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["segment_id"] == "my-scene"
    assert body["word_count"] == 3
    assert len(body["rating"]["scores"]) == 30

    assert (tmp_path / "ratings" / "my-scene.jsonl").exists()
    assert (tmp_path / "corpus" / "my-scene.md").exists()

    listed = client.get("/api/segments").json()
    assert any(s["id"] == "my-scene" for s in listed)

    one = client.get("/api/segments/my-scene").json()
    assert one["text"].strip() == "some prose here"
    assert len(one["ratings"]) == 1


def test_rate_endpoint_appends_on_rerun(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        app_module.rater, "rate",
        lambda **k: _fake_rating(k["segment_id"], k["rater"]),
    )
    payload = {"text": "identical text", "title": "Rerun"}
    client.post("/api/rate", json=payload)
    client.post("/api/rate", json=payload)
    one = client.get("/api/segments/rerun").json()
    assert len(one["ratings"]) == 2  # same segment id -> ratings accrue


def test_rate_endpoint_rejects_id_collision_with_different_text(tmp_path, monkeypatch):
    """A slug/id reused for DIFFERENT text is rejected (409) so a rating can never be
    orphaned from the prose it scored."""
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        app_module.rater, "rate",
        lambda **k: _fake_rating(k["segment_id"], k["rater"]),
    )
    # Two case/punctuation-equivalent titles collide on the slug "chapter-one".
    first = client.post("/api/rate", json={"text": "the first passage", "title": "Chapter One"})
    assert first.status_code == 200
    second = client.post(
        "/api/rate", json={"text": "a totally different passage", "title": "chapter one!!!"}
    )
    assert second.status_code == 409
    # The original segment and its single rating are untouched.
    one = client.get("/api/segments/chapter-one").json()
    assert one["text"].strip() == "the first passage"
    assert len(one["ratings"]) == 1


def test_rate_endpoint_rejects_empty_text(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    assert client.post("/api/rate", json={"text": "   "}).status_code == 400


def test_rate_endpoint_maps_rater_error_to_400(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))

    def boom(**kwargs):
        raise RaterError("ANTHROPIC_API_KEY is not set. Add it to backend/.env.")

    monkeypatch.setattr(app_module.rater, "rate", boom)
    r = client.post("/api/rate", json={"text": "hello world"})
    assert r.status_code == 400
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_segment_not_found_is_404(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    assert client.get("/api/segments/does-not-exist").status_code == 404
