"""The L1 rater — turns a prose segment into a validated `Rating` via Claude structured
output under the frozen manual (DESIGN.md §4.1, §6.1).

The output schema is built dynamically from the axis registry: one required field per
axis, each a `{value, confidence}` object where `value` is a `Literal` int-enum (1–7)
for scalar axes or a `Literal` string-enum for forced-choice axes. Structured outputs
guarantee (a) every axis is present (required fields) and (b) every value is in range
(enum constrained decoding) — so a malformed rating cannot come back.

Interpretation space: this module must NEVER be imported by `lsap.engine`
(enforced by `tests/test_firewall.py`).
"""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, create_model

from lsap.config import settings

from .schema import AxisDef, AxisScore, Rating, compute_flagged

# Aliases and capability tables ------------------------------------------------------

_MODEL_ALIASES = {
    "opus": "claude-opus-4-8",
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-5",
}

# Models that take `thinking: {"type": "adaptive"}`. Haiku 4.5 is intentionally absent —
# it supports neither adaptive thinking nor the effort parameter (verified 2026-07-02).
_ADAPTIVE_THINKING_MODELS = {
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-5",
    "claude-sonnet-4-6",
    "claude-fable-5",
}

# Non-streaming ceiling that keeps requests under SDK HTTP timeouts; leaves ample room
# for adaptive thinking plus the tiny (~1 KB) structured output.
_MAX_TOKENS = 16000


class RaterError(RuntimeError):
    """A rating could not be produced (no key, refusal, empty structured output)."""


def resolve_model(rater: str) -> str:
    return _MODEL_ALIASES.get(rater, rater)


def _supports_adaptive_thinking(model: str) -> bool:
    return model in _ADAPTIVE_THINKING_MODELS


# Dynamic output schema --------------------------------------------------------------

def build_rater_output_model(axes: list[AxisDef]) -> type[BaseModel]:
    """A Pydantic model with one required field per axis id, each `{value, confidence}`."""
    fields: dict[str, Any] = {}
    for a in axes:
        if a.kind == "forced_choice":
            if not a.choices:
                raise ValueError(f"forced-choice axis {a.id} has no choices")
            value_type: Any = Literal[tuple(a.choices)]  # string enum
        else:
            value_type = Literal[1, 2, 3, 4, 5, 6, 7]  # int enum
        axis_model = create_model(
            f"Score_{a.id}",
            value=(value_type, ...),
            confidence=(Literal[1, 2, 3, 4, 5], ...),
        )
        fields[a.id] = (axis_model, ...)
    return create_model("RaterOutput", **fields)


def to_rating(
    output: BaseModel,
    *,
    axes: list[AxisDef],
    segment_id: str,
    rater_id: str,
    created_at: str,
) -> Rating:
    """Convert the structured output into the canonical `Rating` (forced-choice values
    stored as the 1-based index into `choices`)."""
    scores: list[AxisScore] = []
    for a in axes:
        sub = getattr(output, a.id)
        if a.kind == "forced_choice":
            assert a.choices is not None
            value = a.choices.index(sub.value) + 1
        else:
            value = int(sub.value)
        scores.append(AxisScore(axis_id=a.id, value=value, confidence=int(sub.confidence)))
    return Rating(
        segment_id=segment_id,
        rater_id=rater_id,
        scores=scores,
        flagged=compute_flagged(scores),
        created_at=created_at,
    )


# The manual (system prompt) ---------------------------------------------------------

_GOLDEN_RULES = """You are a trained rater applying the LSAP-1 instrument. Your job is to \
measure what is PRESENT in a prose segment, not to judge its quality.

Golden rules:
- No literary judgment. Never ask "is this good?" — only "what is present?".
- Score behavior, not meaning. Ignore author identity and genre reputation.
- No cross-axis contamination: score each axis strictly on its own definition.
- Four-pass workflow: (1) read the segment; (2) mark its structure (sentence, dialogue,
  POV, time, and emotion boundaries); (3) score the axes; (4) score your confidence per
  axis, from 1 (guessing) to 5 (very high).

For every one of the 30 axes return {value, confidence}:
- Scalar axes: value is an integer 1–7 on the anchored scale (anchors given at 1/4/7).
- Forced-choice axes: value is exactly one of the listed options.
- confidence: an integer 1–5.
"""


def build_manual(axes: list[AxisDef]) -> str:
    lines = [_GOLDEN_RULES, "\nThe 30 axes:"]
    for a in axes:
        head = f"\n[{a.id}] {a.name} — {a.definition}"
        lines.append(head)
        if a.kind == "forced_choice" and a.choices:
            lines.append(f"  choices: {', '.join(a.choices)}")
        elif a.anchors:
            anchors = "; ".join(f"{k}={v}" for k, v in sorted(a.anchors.items()))
            lines.append(f"  scale: {anchors}")
        if a.watch_for:
            lines.append(f"  watch for: {'; '.join(a.watch_for)}")
    return "\n".join(lines)


# The call ---------------------------------------------------------------------------

def _default_client() -> Any:
    if not (settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")):
        raise RaterError("ANTHROPIC_API_KEY is not set. Add it to backend/.env.")
    import anthropic

    return anthropic.Anthropic()


def rate(
    *,
    segment_id: str,
    segment_text: str,
    rater: str,
    axes: list[AxisDef],
    created_at: str,
    client: Any | None = None,
) -> Rating:
    """Score `segment_text` on all 30 axes with model `rater` (alias or full id)."""
    if not segment_text.strip():
        raise RaterError("segment text is empty")

    model = resolve_model(rater)
    client = client or _default_client()
    output_model = build_rater_output_model(axes)

    kwargs: dict[str, Any] = dict(
        model=model,
        max_tokens=_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": build_manual(axes),
                "cache_control": {"type": "ephemeral"},  # the manual is stable → cache it
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    "Score this segment on all 30 axes.\n\n"
                    f"<segment>\n{segment_text}\n</segment>"
                ),
            }
        ],
        output_format=output_model,
    )
    if _supports_adaptive_thinking(model):
        kwargs["thinking"] = {"type": "adaptive"}

    try:
        resp = client.messages.parse(**kwargs)
    except RaterError:
        raise
    except Exception as e:  # noqa: BLE001 — surface any SDK/transport error uniformly
        raise RaterError(f"rater call failed: {e}") from e

    output = getattr(resp, "parsed_output", None)
    if output is None:
        stop = getattr(resp, "stop_reason", None)
        raise RaterError(f"rater returned no structured output (stop_reason={stop})")

    return to_rating(
        output, axes=axes, segment_id=segment_id, rater_id=model, created_at=created_at
    )
