from lsap import storage
from lsap.instrument.schema import AxisScore, Rating


def _rating(seg: str, rater: str, *, value: int = 4, axes_version: int = 1) -> Rating:
    scores = [AxisScore(axis_id=f"X{i}", value=value, confidence=5) for i in range(30)]
    return Rating(
        segment_id=seg, rater_id=rater, axes_version=axes_version, scores=scores,
        flagged=False, created_at="2026-07-03T00:00:00Z",
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
    assert storage.latest_ratings("nope") == {}


def test_latest_ratings_newest_wins_per_rater(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    storage.save_rating(_rating("seg-a", "claude-opus-4-8", value=4))
    storage.save_rating(_rating("seg-a", "claude-haiku-4-5", value=3))
    storage.save_rating(_rating("seg-a", "claude-opus-4-8", value=2))  # the re-rate
    latest = storage.latest_ratings("seg-a")
    assert set(latest) == {"claude-opus-4-8", "claude-haiku-4-5"}
    # The appended (newer) rating supersedes — first-wins would return 4 here.
    assert latest["claude-opus-4-8"].scores[0].value == 2
    assert latest["claude-haiku-4-5"].scores[0].value == 3


def test_latest_ratings_never_pools_axes_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("LSAP_DATA_DIR", str(tmp_path))
    storage.save_rating(_rating("seg-a", "claude-opus-4-8", value=4, axes_version=1))
    storage.save_rating(_rating("seg-a", "claude-haiku-4-5", value=3, axes_version=1))
    storage.save_rating(_rating("seg-a", "claude-opus-4-8", value=6, axes_version=2))
    # Default = the newest version present: only the v2 cohort, no v1 haiku mixed in.
    latest = storage.latest_ratings("seg-a")
    assert set(latest) == {"claude-opus-4-8"}
    assert latest["claude-opus-4-8"].axes_version == 2
    # An explicit older cohort is still addressable, unpolluted by v2.
    v1 = storage.latest_ratings("seg-a", axes_version=1)
    assert set(v1) == {"claude-opus-4-8", "claude-haiku-4-5"}
    assert v1["claude-opus-4-8"].scores[0].value == 4


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
