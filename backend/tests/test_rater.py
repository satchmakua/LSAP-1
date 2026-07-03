import types

import pytest

from lsap.instrument.rater import (
    RaterError,
    build_manual,
    build_rater_output_model,
    rate,
    resolve_model,
    to_rating,
)
from lsap.instrument.schema import load_axes

AXES = load_axes()


def _fake_output(axes):
    """A stand-in for the model's structured output — one .value/.confidence per axis."""
    ns = types.SimpleNamespace()
    for a in axes:
        value = a.choices[0] if a.kind == "forced_choice" else 4
        setattr(ns, a.id, types.SimpleNamespace(value=value, confidence=5))
    return ns


class _FakeMessages:
    def __init__(self, output):
        self._output = output
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return types.SimpleNamespace(parsed_output=self._output, stop_reason="end_turn")


class _FakeClient:
    def __init__(self, output):
        self.messages = _FakeMessages(output)


def test_resolve_model_aliases():
    assert resolve_model("opus") == "claude-opus-4-8"
    assert resolve_model("haiku") == "claude-haiku-4-5"
    assert resolve_model("claude-opus-4-8") == "claude-opus-4-8"


def test_build_output_model_has_a_field_per_axis():
    model = build_rater_output_model(AXES)
    assert set(model.model_fields) == {a.id for a in AXES}


def test_build_manual_mentions_every_axis_and_rules():
    manual = build_manual(AXES)
    assert "No literary judgment" in manual
    for a in AXES:
        assert f"[{a.id}]" in manual
    assert "awe, dread, grief" in manual  # A3 choices rendered


def test_to_rating_indexes_forced_choice_values():
    out = _fake_output(AXES)
    a3 = next(a for a in AXES if a.id == "A3")
    # Pick the 3rd choice -> stored as 1-based index 3.
    out.A3 = types.SimpleNamespace(value=a3.choices[2], confidence=3)
    rating = to_rating(out, axes=AXES, segment_id="s", rater_id="m", created_at="t")
    a3_score = next(s for s in rating.scores if s.axis_id == "A3")
    assert a3_score.value == 3
    assert a3_score.confidence == 3
    # Scalar axis passes through unchanged.
    l1 = next(s for s in rating.scores if s.axis_id == "L1")
    assert l1.value == 4


def test_rate_produces_complete_rating_and_sends_thinking_for_opus():
    client = _FakeClient(_fake_output(AXES))
    rating = rate(
        segment_id="s1",
        segment_text="Some prose to score.",
        rater="claude-opus-4-8",
        axes=AXES,
        created_at="2026-07-03T00:00:00Z",
        client=client,
    )
    assert len(rating.scores) == 30
    assert {s.axis_id for s in rating.scores} == {a.id for a in AXES}
    assert rating.rater_id == "claude-opus-4-8"
    assert rating.flagged is False  # all confidence 5

    call = client.messages.calls[0]
    assert call["thinking"] == {"type": "adaptive"}
    assert call["system"][0]["cache_control"]["type"] == "ephemeral"
    assert call["model"] == "claude-opus-4-8"


def test_rate_omits_thinking_for_haiku():
    client = _FakeClient(_fake_output(AXES))
    rate(
        segment_id="s1",
        segment_text="x",
        rater="haiku",
        axes=AXES,
        created_at="t",
        client=client,
    )
    call = client.messages.calls[0]
    assert "thinking" not in call
    assert call["model"] == "claude-haiku-4-5"


def test_rate_rejects_empty_text():
    client = _FakeClient(_fake_output(AXES))
    with pytest.raises(RaterError):
        rate(
            segment_id="s", segment_text="   ", rater="opus",
            axes=AXES, created_at="t", client=client,
        )


def test_rate_raises_on_missing_structured_output():
    client = _FakeClient(_fake_output(AXES))
    client.messages.parse = lambda **k: types.SimpleNamespace(
        parsed_output=None, stop_reason="refusal"
    )
    with pytest.raises(RaterError):
        rate(
            segment_id="s", segment_text="hi", rater="opus",
            axes=AXES, created_at="t", client=client,
        )
