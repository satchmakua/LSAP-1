"""Slider dials -> generation RULES (not descriptions). DESIGN.md §6.3.

The pivot of the engine: `c1 high` must become *"nested clauses allowed, stack metaphors,
leave meaning implicit"* — instructions a renderer can obey — never *"be dense"*.

FIREWALL (Charter P4): this package imports nothing from `lsap.instrument`,
`lsap.coordinates` or `lsap.storage`. The dials are named c1..c5 for the writer's
intuition, but they are CONTROL INPUTS to operators B1..B5, computed by a path with zero
dependency on the instrument's fitted PCA. Enforced by `tests/test_firewall.py`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Band = Literal["low", "med", "high", "extreme"]
BANDS: tuple[Band, ...] = ("low", "med", "high", "extreme")

# The five scene phases (DESIGN §6.3): emotional energy rises, then leaves a residue.
PHASES: tuple[str, ...] = ("establishment", "drift", "pressure", "breakdown", "residue")
_PHASE_BASE = {"establishment": 0.5, "drift": 1.5, "pressure": 3.0, "breakdown": 4.5,
               "residue": 3.5}


class Dials(BaseModel):
    """The only input the UI sends the engine."""

    c1: float = Field(ge=0.0, le=1.0)  # compression (operator B1)
    c2: float = Field(ge=0.0, le=1.0)  # temporal structure (B2)
    c3: float = Field(ge=0.0, le=1.0)  # interiorization (B3)
    c4: float = Field(ge=0.0, le=1.0)  # (de)stabilization (B4)
    c5: float = Field(ge=0.0, le=1.0)  # affective amplification (B5)
    style_seed: str | None = None


class ConstraintSpec(BaseModel):
    """Compiled, renderer-facing rules. No prose adjectives — only instructions."""

    bands: dict[str, Band]
    rules: dict[str, list[str]]
    agential_pressure: Band  # B6, derived (blueprint §8: the hidden sixth operator)
    perception: str  # PL filter
    registers: list[str]  # LR palette to rotate through
    phases: list[str]
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
    return {k: to_band(getattr(d, k)) for k in ("c1", "c2", "c3", "c4", "c5")}


# --- rule tables: one operator per dial, one rule set per band ------------------------

_RULES: dict[str, dict[Band, list[str]]] = {
    "c1": {  # B1 compression / expansion
        "low": ["One idea per sentence.", "Short declaratives; avoid subordination.",
                "No metaphor — name the thing plainly.", "State meaning explicitly."],
        "med": ["Mix short and medium sentences.", "At most one figure per paragraph.",
                "Some meaning may be left implied."],
        "high": ["Nested clauses are allowed.", "Stack metaphors.",
                 "Leave meaning implicit.", "Compress several ideas into one sentence."],
        "extreme": ["Write long, deeply subordinated periods.",
                    "Metaphor upon metaphor; let figures breed.",
                    "Meaning is carried by omission — state almost nothing outright.",
                    "Maximum semantic density per sentence."],
    },
    "c2": {  # B2 temporal structure
        "low": ["Strict chronological order.", "No flashback.", "Time passes evenly."],
        "med": ["Mostly linear; one small ellipsis is allowed."],
        "high": ["Reorder events; flashback and ellipsis are allowed.",
                 "Dilate one moment and skip another."],
        "extreme": ["Achronological: loop and repeat moments.",
                    "Time is unreliable; a moment may recur altered."],
    },
    "c3": {  # B3 consciousness interiorization
        "low": ["Report only what a camera would record.", "No access to thought.",
                "No interior commentary."],
        "med": ["Brief interiority; the paragraph stays mostly exterior."],
        "high": ["Stay inside the perceiving mind.",
                 "Thought and perception interleave."],
        "extreme": ["Unbroken stream of consciousness.",
                    "The world arrives only as perception, never as report."],
    },
    "c4": {  # B4 epistemic (de)stabilization
        "low": ["The world obeys consistent rules.", "No contradiction.",
                "Facts stay fixed."],
        "med": ["One small inconsistency may pass unremarked."],
        "high": ["Introduce a contradiction and do not explain it.",
                 "An object's state need not match what was said of it before."],
        "extreme": ["Reality-rules bend; paradox is ordinary.",
                    "The scene may contradict itself outright and continue."],
    },
    "c5": {  # B5 affective amplification
        "low": ["Flat affect.", "Do not name an emotion.",
                "Feeling, if any, is left to the reader."],
        "med": ["Restrained emotion, implied by selection of detail."],
        "high": ["Emotion colours perception; what is noticed is what is felt."],
        "extreme": ["The world is read entirely through feeling.",
                    "Intensity overwhelms observation."],
    },
    "b6": {  # B6 agential pressure (derived) — what makes a trap a trap
        "low": ["The character acts freely and the world yields."],
        "med": ["Action mostly succeeds; there is minor friction."],
        "high": ["Action is deflected; effort meets resistance."],
        "extreme": ["Action is impossible; every attempt defers to another."],
    },
}


def agential_pressure(d: Dials) -> Band:
    """B6 is not a slider — it emerges. High destabilization plus a *blocked* temporal
    structure (low c2) is what turns an unstable state into a trap (blueprint §8)."""
    return to_band((d.c4 + (1.0 - d.c2)) / 2.0)


def perception_filter(d: Dials) -> str:
    """The PL filter: how the point of view distorts the world state."""
    if d.c4 >= 0.7:
        return "modernist (fragmented cognition; the scene will not hold still)"
    if d.c3 >= 0.6 and d.c5 >= 0.6:
        return "expressionist (the environment mirrors the feeling)"
    if d.c3 >= 0.6:
        return "sebald (documentary tone, emotion suppressed beneath the record)"
    if d.c5 >= 0.6:
        return "noir (moral weight accrues to objects)"
    return "realist (high fidelity to the world state)"


def register_palette(d: Dials) -> list[str]:
    """The LR palette. At least two, so the rotation rule always has somewhere to go."""
    out: list[str] = []
    if d.c1 >= 0.6:
        out.append("elevated literary")
    if d.c1 < 0.4:
        out.append("plain realist")
    if d.c4 >= 0.6:
        out.append("fragmented modernist")
    if d.c5 >= 0.6:
        out.append("noir-compressed")
    if d.c3 < 0.4:
        out.append("clinical")
    for fallback in ("plain realist", "elevated literary"):
        if len(out) < 2 and fallback not in out:
            out.append(fallback)
    return out


def phase_energy(phase: str, c5: float) -> float:
    """Emotional-field level (0–5) for a phase, scaled by the affect dial."""
    base = _PHASE_BASE.get(phase, 1.0)
    return round(min(5.0, max(0.0, base * (0.5 + c5))), 1)


def compile_constraints(d: Dials) -> ConstraintSpec:
    """Dials -> renderer-facing rules. Pure and deterministic."""
    bands = to_bands(d)
    b6 = agential_pressure(d)
    rules = {dial: list(_RULES[dial][band]) for dial, band in bands.items()}
    rules["b6"] = list(_RULES["b6"][b6])
    return ConstraintSpec(
        bands=bands,
        rules=rules,
        agential_pressure=b6,
        perception=perception_filter(d),
        registers=register_palette(d),
        phases=list(PHASES),
        style_seed=d.style_seed,
    )
