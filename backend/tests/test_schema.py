from collections import Counter

from lsap.instrument.schema import (
    AxisScore,
    Rating,
    compute_flagged,
    load_axes,
    load_axes_version,
)


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
    assert r.axes_version == 1  # defaulted — pre-M5 stored ratings parse as the v1 cohort


def test_stored_rating_without_axes_version_parses_as_v1():
    # A literal pre-M5 JSONL line: no axes_version field anywhere.
    line = (
        '{"segment_id": "s", "rater_id": "claude-opus-4-8", "scores": '
        '[{"axis_id": "L1", "value": 3, "confidence": 4}], '
        '"flagged": false, "created_at": "2026-07-03T00:00:00Z"}'
    )
    assert Rating.model_validate_json(line).axes_version == 1


def test_axes_registry_carries_a_version():
    # M5 re-anchored L1/L3, so the registry must be past its initial revision.
    assert load_axes_version() >= 2
