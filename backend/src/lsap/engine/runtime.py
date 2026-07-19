"""L6 runtime cognition — the Style Engine (DESIGN.md §6.3, blueprint §11.1).

A scene is *resolved* from five stateful subsystems rather than written linearly:

  WS  World State       ground truth: concrete facts + physical objects, no emotion
  PL  Perception Layer  the POV filter (compiled from the dials)
  MF  Memory Field      prior object states — the source of uncanny continuity
  EF  Emotional Field   0–5, the physics of attention; follows the scene-phase curve
  LR  Language Register rotates every paragraph, so no register can persist

The state machine is deterministic: phase, emotional energy, register and the memory
field advance in code between paragraphs, and Claude is only the *rendering layer* for
each step. That is what makes this a simulator rather than one long prompt. Objects, not
plot, carry continuity.

FIREWALL (Charter P4): imports nothing from `lsap.instrument` / `lsap.coordinates` /
`lsap.storage`. Only `lsap.config` (shared) plus the SDK.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel

from lsap.config import settings

from .compiler import PHASES, ConstraintSpec, Dials, compile_constraints, phase_energy

_MAX_TOKENS = 1200  # one paragraph per call; the loop is the long-running part


class EngineError(RuntimeError):
    """Generation could not be produced (no key, refusal, empty render)."""


class WorldState(BaseModel):
    """WS — ground truth. Concrete and unemotional, per the blueprint."""

    facts: list[str]
    objects: list[str]


class Paragraph(BaseModel):
    """One rendered step, carrying the state that produced it."""

    index: int
    phase: str
    language_register: str  # not `register`: that shadows BaseModel.register
    emotional_energy: float
    text: str
    objects_seen: list[str]
    memory_note: str | None = None


class GenerationRun(BaseModel):
    dials: Dials
    spec: ConstraintSpec
    situation: str
    world: WorldState
    paragraphs: list[Paragraph]


# --- the deterministic state machine --------------------------------------------------


def phase_for(index: int, total: int) -> str:
    """Map a paragraph index onto the five-phase curve; the last is always the residue."""
    if total <= 1:
        return PHASES[0]
    if index >= total - 1:
        return PHASES[-1]
    step = int(index * (len(PHASES) - 1) / max(1, total - 1))
    return PHASES[min(len(PHASES) - 2, step)]


def register_for(spec: ConstraintSpec, index: int) -> str:
    """LR rotation — a register never persists into the next paragraph."""
    return spec.registers[index % len(spec.registers)]


def memory_note_for(
    world: WorldState, index: int, phase: str, *, destabilize: bool
) -> str | None:
    """MF: objects carry continuity. Under a stable world that means recurrence; once the
    destabilization dial is up, memory starts disagreeing with the world."""
    if not world.objects:
        return None
    obj = world.objects[index % len(world.objects)]
    if not destabilize:
        if phase in ("pressure", "breakdown", "residue"):
            return f"{obj} recurs, in exactly the state it was left in."
        return None
    if phase == "pressure":
        return (
            f"Memory insists {obj} was in a different state earlier. "
            "Let the discrepancy stand; do not explain it."
        )
    if phase == "breakdown":
        return f"Memory now contradicts the world outright about {obj}. Do not resolve it."
    if phase == "residue":
        return f"End on {obj}, its state unresolved."
    return None


def objects_seen_in(world: WorldState, text: str) -> list[str]:
    low = text.lower()
    return [
        o for o in world.objects
        if any(w in low for w in o.lower().split() if len(w) > 3)
    ]


# --- the rendering layer --------------------------------------------------------------


def _default_client() -> Any:
    key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise EngineError("ANTHROPIC_API_KEY is not set. Add it to backend/.env.")
    import anthropic

    return anthropic.Anthropic(api_key=key)


_SEED_SYSTEM = (
    "You establish the ground-truth world state for a scene. Report only what is "
    "physically the case: concrete, observable, unemotional. No interpretation, no "
    "feeling, no metaphor."
)

_RENDER_SYSTEM = (
    "You are the rendering layer of a prose engine. You do not invent structure — you "
    "render the given state under the given constraints. Obey every rule literally. "
    "Output ONLY the prose of the next paragraph: no heading, no commentary, no "
    "restatement of the instructions, no quotation marks around the whole."
)


def seed_world(client: Any, situation: str, model: str) -> WorldState:
    """WS: 3–7 concrete facts and at least two physical objects."""
    try:
        resp = client.messages.parse(
            model=model,
            max_tokens=1000,
            system=_SEED_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Situation: {situation}\n\n"
                        "Establish the world state: 3–7 concrete facts, and at least two "
                        "physical objects present in the scene."
                    ),
                }
            ],
            output_format=WorldState,
        )
    except Exception as e:  # noqa: BLE001 — surface SDK/transport errors uniformly
        raise EngineError(f"world seeding failed: {e}") from e
    world = getattr(resp, "parsed_output", None)
    if world is None or not world.facts:
        raise EngineError("world seeding returned no structured output")
    return world


def _render_prompt(
    *,
    spec: ConstraintSpec,
    situation: str,
    world: WorldState,
    phase: str,
    energy: float,
    register: str,
    memory_note: str | None,
    previous: str,
) -> str:
    lines = [
        f"SITUATION: {situation}",
        "",
        "WORLD STATE (ground truth — do not contradict it except where a rule says to):",
        *(f"  - {f}" for f in world.facts),
        f"  objects: {', '.join(world.objects)}",
        "",
        f"PERCEPTION FILTER: {spec.perception}",
        f"SCENE PHASE: {phase} (emotional energy {energy}/5)",
        f"LANGUAGE REGISTER for this paragraph: {register}",
    ]
    if spec.style_seed:
        lines.append(f"STYLE SEED: {spec.style_seed}")
    if memory_note:
        lines.append(f"MEMORY FIELD: {memory_note}")
    lines += ["", "RULES (obey all):"]
    for dial, rules in spec.rules.items():
        for r in rules:
            lines.append(f"  [{dial}] {r}")
    if previous:
        lines += ["", "PREVIOUS PARAGRAPH (continue from it):", previous]
    lines += ["", "Write the next paragraph only (about 90–140 words)."]
    return "\n".join(lines)


def render_paragraph(client: Any, model: str, prompt: str) -> str:
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            system=_RENDER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:  # noqa: BLE001
        raise EngineError(f"render failed: {e}") from e
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    if not text:
        raise EngineError("renderer returned empty prose")
    return text


# --- the loop -------------------------------------------------------------------------


def generate(
    *,
    dials: Dials,
    situation: str,
    paragraphs: int = 5,
    client: Any | None = None,
    model: str | None = None,
) -> GenerationRun:
    """Compile the dials, seed the world, then render paragraph by paragraph, advancing
    the state machine between steps."""
    if not situation.strip():
        raise EngineError("situation is required")
    if paragraphs < 1:
        raise EngineError("paragraphs must be >= 1")

    spec = compile_constraints(dials)
    client = client or _default_client()
    model = model or settings.renderer_model

    world = seed_world(client, situation.strip(), model)
    out: list[Paragraph] = []
    previous = ""
    for i in range(paragraphs):
        phase = phase_for(i, paragraphs)
        register = register_for(spec, i)
        energy = phase_energy(phase, dials.c5)
        note = memory_note_for(world, i, phase, destabilize=dials.c4 >= 0.4)
        text = render_paragraph(
            client,
            model,
            _render_prompt(
                spec=spec, situation=situation.strip(), world=world, phase=phase,
                energy=energy, register=register, memory_note=note, previous=previous,
            ),
        )
        out.append(
            Paragraph(
                index=i, phase=phase, language_register=register, emotional_energy=energy,
                text=text, objects_seen=objects_seen_in(world, text), memory_note=note,
            )
        )
        previous = text

    return GenerationRun(
        dials=dials, spec=spec, situation=situation.strip(), world=world, paragraphs=out
    )
