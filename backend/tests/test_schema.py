from collections import Counter

from lsap.instrument.schema import AxisScore, Rating, compute_flagged, load_axes


def test_load_axes_has_30_across_six_fields():
    axes = load_axes()
    assert len(axes) == 30
    counts = Counter(a.field for a in axes)
    assert all(counts[f] == 5 for f in "LNCPAS"), counts
    # Every scalar axis carries anchors; every forced-choice axis carries choices.
    for a in axes:
        if a.kind == "scalar":
            assert a.anchors and {1, 4, 7} <= set(a.anchors)
        else:
            assert a.choices


def test_forced_choice_axes_are_exactly_three():
    fc = {a.id for a in load_axes() if a.kind == "forced_choice"}
    assert fc == {"A3", "A5", "S5"}


def test_axis_ids_are_unique():
    ids = [a.id for a in load_axes()]
    assert len(ids) == len(set(ids))


def test_rating_validates_and_flag_rule():
    low = [AxisScore(axis_id=f"X{i}", value=4, confidence=1) for i in range(30)]
    assert compute_flagged(low) is True  # all low-confidence -> flagged
    high = [AxisScore(axis_id=f"X{i}", value=4, confidence=5) for i in range(30)]
    assert compute_flagged(high) is False

    r = Rating(
        segment_id="s1",
        rater_id="claude-opus-4-8",
        scores=high,
        flagged=compute_flagged(high),
        created_at="2026-07-02T00:00:00Z",
    )
    assert r.flagged is False
    assert len(r.scores) == 30
