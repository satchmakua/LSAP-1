from lsap import storage
from lsap.instrument.schema import AxisScore, Rating


def _rating(seg: str, rater: str) -> Rating:
    scores = [AxisScore(axis_id=f"X{i}", value=4, confidence=5) for i in range(30)]
    return Rating(
        segment_id=seg, rater_id=rater, scores=scores, flagged=False,
        created_at="2026-07-03T00:00:00Z",
    )


def test_save_and_load_ratings_append(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    storage.save_rating(_rating("seg-a", "claude-opus-4-8"))
    storage.save_rating(_rating("seg-a", "claude-haiku-4-5"))
    got = storage.load_ratings("seg-a")
    assert [r.rater_id for r in got] == ["claude-opus-4-8", "claude-haiku-4-5"]
    assert (tmp_path / "ratings" / "seg-a.jsonl").exists()


def test_load_ratings_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    assert storage.load_ratings("nope") == []


def test_save_segment_is_write_once(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    storage.save_segment("seg-a", "one two three", source="pasted", created_at="t")
    storage.save_segment("seg-a", "totally different text", source="pasted", created_at="t")
    seg = storage.load_segment("seg-a")
    assert seg is not None
    assert seg["id"] == "seg-a"
    assert seg["text"].strip() == "one two three"
    assert seg["word_count"] == 3


def test_list_segments_cross_references_ratings(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    storage.save_segment("seg-a", "a b c", source="pasted", created_at="t")
    storage.save_rating(_rating("seg-a", "claude-opus-4-8"))
    listed = storage.list_segments()
    assert len(listed) == 1
    assert listed[0]["id"] == "seg-a"
    assert listed[0]["rater_ids"] == ["claude-opus-4-8"]
    assert listed[0]["word_count"] == 3


def test_slugify():
    assert storage.slugify("The Dead — James Joyce!", fallback="x") == "the-dead-james-joyce"
    assert storage.slugify("!!!", fallback="fb") == "fb"
