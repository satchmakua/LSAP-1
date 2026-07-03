"""The measurement contract (DESIGN.md §4.1).

A segment (~1,000–3,000 words) becomes 30 anchored scores with per-axis confidence.
Axes are DATA (`axes.yaml`), so tuning the instrument is a data change, not a rewrite.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field

FieldCode = Literal["L", "N", "C", "P", "A", "S"]
# Language / Narrative / Consciousness / Philosophy / Affective / Stylistic

AXES_PATH = Path(__file__).parent / "axes.yaml"

Score7 = Annotated[int, Field(ge=1, le=8)]  # 7-pt scalar, OR 1-based choice index (A3 has 8)
Confidence = Annotated[int, Field(ge=1, le=5)]  # 1 guessing .. 5 very high


class AxisDef(BaseModel):
    """One of the 30 axes, loaded from `axes.yaml`."""

    id: str  # "L1", "N3", "A3", ...
    field: FieldCode
    name: str
    kind: Literal["scalar", "forced_choice"]
    definition: str  # what is PRESENT, never whether it is good
    anchors: dict[int, str] | None = None  # {1: "...", 4: "...", 7: "..."} for scalar
    choices: list[str] | None = None  # options for forced-choice axes
    watch_for: list[str] = Field(default_factory=list)  # contamination warnings


class AxisScore(BaseModel):
    axis_id: str
    value: Score7
    confidence: Confidence


class Rating(BaseModel):
    """A complete rating of one segment by one rater."""

    segment_id: str
    rater_id: str  # "claude-opus-4-8" | "claude-haiku-4-5" | "human:sh"
    scores: list[AxisScore]  # 30, in fixed field order L -> N -> C -> P -> A -> S
    flagged: bool = False  # True if confidence <= 2 on > 40% of axes
    created_at: str  # ISO 8601, injected by the caller (no wall-clock in pure code)


def load_axes(path: Path = AXES_PATH) -> list[AxisDef]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [AxisDef(**a) for a in data["axes"]]


def compute_flagged(scores: list[AxisScore]) -> bool:
    """A segment is flagged for review if confidence is <= 2 on more than 40% of axes."""
    if not scores:
        return False
    low = sum(1 for s in scores if s.confidence <= 2)
    return low / len(scores) > 0.40
