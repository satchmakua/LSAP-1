"""Slider dials -> generation RULES (not descriptions). DESIGN.md §6.3.

FIREWALL: imports nothing from `lsap.instrument` / `lsap.coordinates`. The dials are
named c1..c5 for the writer's intuition, but they are CONTROL INPUTS to operators
B1..B5 — computed by a path with zero dependency on the instrument's fitted PCA.
Full compiler + runtime cognition land in M4 (see ROADMAP.md).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Band = Literal["low", "med", "high", "extreme"]


class Dials(BaseModel):
    """The only input the UI sends the engine."""

    c1: float = Field(ge=0.0, le=1.0)  # compression (operator B1)
    c2: float = Field(ge=0.0, le=1.0)  # temporal structure (B2)
    c3: float = Field(ge=0.0, le=1.0)  # interiorization (B3)
    c4: float = Field(ge=0.0, le=1.0)  # (de)stabilization (B4)
    c5: float = Field(ge=0.0, le=1.0)  # affective amplification (B5)
    style_seed: str | None = None


def to_band(v: float) -> Band:
    if v < 0.25:
        return "low"
    if v < 0.55:
        return "med"
    if v < 0.85:
        return "high"
    return "extreme"


def to_bands(d: Dials) -> dict[str, Band]:
    """Normalize each dial to a control band. Real behavior, exercised in tests."""
    return {k: to_band(getattr(d, k)) for k in ("c1", "c2", "c3", "c4", "c5")}


def compile_constraints(d: Dials) -> dict:
    """Turn dials into generation rules, e.g. c1=high -> nested clauses allowed,
    metaphor stacking, implicit meaning encouraged. Fleshed out in M4."""
    raise NotImplementedError("Full constraint compiler implemented in M4 — see ROADMAP.md")
