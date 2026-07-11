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
    """Stand-in for the model's structured output: a `.scores` list of
    {axis_id, value, confidence} (forced-choice value is a 1-based option index)."""
    scores = [
        types.SimpleNamespace(
            axis_id=a.id,
            value=1 if a.kind == "forced_choice" else 4,
            confidence=5,
        )
        for a in axes
    ]
    return types.SimpleNamespace(scores=scores)


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


def test_build_output_model_is_a_scores_list_over_all_axes():
    model = build_rater_output_model(AXES)
    assert set(model.model_fields) == {"scores"}
    schema = model.model_json_schema()
    scored = schema["$defs"]["ScoredAxis"]["properties"]
    # axis_id is a 30-member enum; value/confidence are plain integers (grammar-size fix).
    assert set(scored["axis_id"]["enum"]) == {a.id for a in AXES}
    assert scored["value"]["type"] == "integer"
    assert "enum" not in scored["value"]


def test_build_manual_mentions_every_axis_and_rules():
    manual = build_manual(AXES)
    assert "No literary judgment" in manual
    for a in AXES:
        assert f"[{a.id}]" in manual
    assert "1=awe" in manual  # A3 choices rendered as numbered options


def test_to_rating_maps_forced_choice_index_and_scalar_value():
    out = _fake_output(AXES)
    a3 = next(s for s in out.scores if s.axis_id == "A3")
    a3.value, a3.confidence = 3, 3  # model returns the 1-based option number, stored as-is
    rating = to_rating(out, axes=AXES, segment_id="s", rater_id="m", created_at="t")
    by = {s.axis_id: s for s in rating.scores}
    assert by["A3"].value == 3 and by["A3"].confidence == 3
    assert by["L1"].value == 4  # scalar passes through


def test_to_rating_clamps_out_of_range_values():
    out = _fake_output(AXES)
    for s in out.scores:
        if s.axis_id == "L1":
            s.value, s.confidence = 9, 0
        if s.axis_id == "N1":
            s.value, s.confidence = 0, 7
    rating = to_rating(out, axes=AXES, segment_id="s", rater_id="m", created_at="t")
    by = {s.axis_id: s for s in rating.scores}
    assert by["L1"].value == 7 and by["L1"].confidence == 1
    assert by["N1"].value == 1 and by["N1"].confidence == 5


def test_to_rating_raises_on_missing_axis():
    out = _fake_output(AXES)
    out.scores = [s for s in out.scores if s.axis_id != "S5"]  # drop one axis
    with pytest.raises(RaterError):
        to_rating(out, axes=AXES, segment_id="s", rater_id="m", created_at="t")


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


def test_default_client_requires_a_key(monkeypatch):
    from lsap.instrument import rater as rmod

    monkeypatch.setattr(rmod.settings, "anthropic_api_key", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RaterError):
        rmod._default_client()


def test_default_client_passes_configured_key_to_sdk(monkeypatch):
    from lsap.instrument import rater as rmod

    monkeypatch.setattr(rmod.settings, "anthropic_api_key", "sk-ant-test-key")
    client = rmod._default_client()
    # The SDK stores the key it was constructed with; confirm ours reached it (rather
    # than the SDK falling back to an unset process env var).
    assert client.api_key == "sk-ant-test-key"
