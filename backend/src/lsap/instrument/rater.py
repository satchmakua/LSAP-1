"""The L1 rater — turns a prose segment into a validated `Rating` via Claude structured
output under the frozen manual (DESIGN.md §4.1, §6.1).

The output schema is a `scores` list of `{axis_id, value, confidence}` objects, where
`axis_id` is a `Literal` enum of the 30 axis ids. A flat list (rather than an object with
30 required properties, or per-axis int-enums) keeps the strict-output grammar under
Anthropic's size cap — both of those shapes trip "compiled grammar is too large". `value`
is a plain integer: the 1–7 anchored score for scalar axes, or the 1-based option number
for forced-choice axes (the manual numbers the choices). `to_rating` checks that all 30
axes are present and clamps values, so a malformed rating cannot come back.

Interpretation space: this module must NEVER be imported by `lsap.engine`
(enforced by `tests/test_firewall.py`).
"""

from __future__ import annotations

import os
from typing import Any, Literal

from pydantic import BaseModel, create_model

from lsap.config import settings

from .schema import AxisDef, AxisScore, Rating, compute_flagged, load_axes_version

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
    """A `{scores: list[{axis_id, value, confidence}]}` model. `axis_id` is a Literal enum
    of the 30 ids; a flat list keeps the strict-output grammar under Anthropic's size cap
    (an object with 30 required properties, or per-axis int-enums, exceeds it)."""
    axis_ids = tuple(a.id for a in axes)
    scored_axis = create_model(
        "ScoredAxis",
        axis_id=(Literal[axis_ids], ...),  # enum over the 30 ids — one small enum, not 30
        value=(int, ...),
        confidence=(int, ...),
    )
    return create_model("RaterOutput", scores=(list[scored_axis], ...))


def to_rating(
    output: BaseModel,
    *,
    axes: list[AxisDef],
    segment_id: str,
    rater_id: str,
    created_at: str,
    axes_version: int,
) -> Rating:
    """Convert the structured output into the canonical `Rating`. Checks that every axis
    is present and clamps values; forced-choice values are the 1-based index into `choices`."""
    by_id = {s.axis_id: s for s in output.scores}
    scores: list[AxisScore] = []
    for a in axes:
        sub = by_id.get(a.id)
        if sub is None:
            raise RaterError(f"rating is missing axis {a.id}")
        if a.kind == "forced_choice":
            assert a.choices is not None
            value = min(len(a.choices), max(1, int(sub.value)))  # 1-based option index
        else:
            value = min(7, max(1, int(sub.value)))  # clamp to the 1–7 anchored scale
        confidence = min(5, max(1, int(sub.confidence)))  # clamp to 1–5
        scores.append(AxisScore(axis_id=a.id, value=value, confidence=confidence))
    return Rating(
        segment_id=segment_id,
        rater_id=rater_id,
        axes_version=axes_version,
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

Return a `scores` list with exactly one entry per axis — all 30 — each with
{axis_id, value, confidence}:
- axis_id: the axis's id, e.g. "L1" or "A3".
- value: for a scalar axis, an integer 1–7 on the anchored scale (anchors given at 1/4/7);
  for a forced-choice axis, the NUMBER (1-based) of your chosen option from its list.
- confidence: an integer 1–5.
"""


def build_manual(axes: list[AxisDef]) -> str:
    lines = [_GOLDEN_RULES, "\nThe 30 axes:"]
    for a in axes:
        head = f"\n[{a.id}] {a.name} — {a.definition}"
        lines.append(head)
        if a.kind == "forced_choice" and a.choices:
            numbered = "; ".join(f"{i + 1}={c}" for i, c in enumerate(a.choices))
            lines.append(f"  choices (return the number): {numbered}")
        elif a.anchors:
            anchors = "; ".join(f"{k}={v}" for k, v in sorted(a.anchors.items()))
            lines.append(f"  scale: {anchors}")
        if a.watch_for:
            lines.append(f"  watch for: {'; '.join(a.watch_for)}")
    return "\n".join(lines)


# The call ---------------------------------------------------------------------------

def _default_client() -> Any:
    key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RaterError("ANTHROPIC_API_KEY is not set. Add it to backend/.env.")
    import anthropic

    # Pass the key explicitly: it may come from backend/.env (loaded into settings) rather
    # than the process environment, which is all the SDK's zero-arg constructor reads.
    return anthropic.Anthropic(api_key=key)


def rate(
    *,
    segment_id: str,
    segment_text: str,
    rater: str,
    axes: list[AxisDef],
    created_at: str,
    client: Any | None = None,
    axes_version: int | None = None,
) -> Rating:
    """Score `segment_text` on all 30 axes with model `rater` (alias or full id).
    The rating is stamped with `axes_version` (default: the registry's current one), so
    ratings scored under different anchors can never be silently pooled."""
    if not segment_text.strip():
        raise RaterError("segment text is empty")
    if axes_version is None:
        axes_version = load_axes_version()

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
        output, axes=axes, segment_id=segment_id, rater_id=model, created_at=created_at,
        axes_version=axes_version,
    )
