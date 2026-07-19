import types

import pytest

from lsap.engine.compiler import (
    PHASES,
    Dials,
    agential_pressure,
    compile_constraints,
    perception_filter,
    phase_energy,
    register_palette,
    to_band,
)
from lsap.engine.presets import load_presets
from lsap.engine.runtime import (
    EngineError,
    WorldState,
    generate,
    memory_note_for,
    objects_seen_in,
    phase_for,
    register_for,
)

FLAT = Dials(c1=0.05, c2=0.05, c3=0.05, c4=0.05, c5=0.05)
DENSE = Dials(c1=0.95, c2=0.9, c3=0.95, c4=0.9, c5=0.9)
WORLD = WorldState(
    facts=["A door is closed.", "A glass sits on a table."],
    objects=["the glass", "the door"],
)


class _FakeMessages:
    def __init__(self):
        self.parse_calls: list[dict] = []
        self.create_calls: list[dict] = []

    def parse(self, **k):
        self.parse_calls.append(k)
        return types.SimpleNamespace(parsed_output=WORLD)

    def create(self, **k):
        self.create_calls.append(k)
        n = len(self.create_calls)
        return types.SimpleNamespace(
            content=[
                types.SimpleNamespace(
                    type="text", text=f"Paragraph {n}. The glass stands on the table."
                )
            ]
        )


class _FakeClient:
    def __init__(self):
        self.messages = _FakeMessages()


# --- compiler -------------------------------------------------------------------------


def test_bands_partition_the_dial():
    assert (to_band(0.0), to_band(0.3), to_band(0.7), to_band(1.0)) == (
        "low", "med", "high", "extreme",
    )


def test_compiled_rules_are_instructions_and_differ_by_band():
    flat = compile_constraints(FLAT)
    dense = compile_constraints(DENSE)
    assert flat.rules["c1"] != dense.rules["c1"]
    # low compression forbids metaphor; extreme compression demands it
    assert any("No metaphor" in r for r in flat.rules["c1"])
    assert any("Metaphor upon metaphor" in r for r in dense.rules["c1"])
    # low interiority is camera-only; extreme is stream of consciousness
    assert any("camera" in r for r in flat.rules["c3"])
    assert any("stream of consciousness" in r.lower() for r in dense.rules["c3"])
    # every rule is an instruction, not an adjective
    assert all(r.endswith(".") for rules in flat.rules.values() for r in rules)


def test_agential_pressure_is_derived_not_dialled():
    """B6 emerges from destabilization against blocked time (blueprint §8)."""
    trap = Dials(c1=0.4, c2=0.05, c3=0.5, c4=0.9, c5=0.4)  # unstable + blocked
    free = Dials(c1=0.4, c2=0.95, c3=0.5, c4=0.05, c5=0.4)  # stable + fluid
    assert agential_pressure(trap) == "extreme"
    assert agential_pressure(free) == "low"
    assert "b6" in compile_constraints(trap).rules


def test_perception_filter_and_register_palette():
    assert "modernist" in perception_filter(DENSE)
    assert "realist" in perception_filter(FLAT)
    for d in (FLAT, DENSE):
        assert len(register_palette(d)) >= 2  # rotation always has somewhere to go


def test_phase_energy_follows_the_curve_and_scales_with_affect():
    assert phase_energy("establishment", 0.9) < phase_energy("breakdown", 0.9)
    assert phase_energy("breakdown", 0.1) < phase_energy("breakdown", 0.9)
    assert 0.0 <= phase_energy("breakdown", 1.0) <= 5.0


def test_presets_load_and_are_valid_dials():
    presets = load_presets()
    assert len(presets) >= 4
    ids = {p.id for p in presets}
    assert {"minimal", "baroque"} <= ids
    assert compile_constraints(next(p for p in presets if p.id == "trap").dials)


# --- state machine --------------------------------------------------------------------


def test_phase_for_walks_the_five_phases_and_ends_on_residue():
    got = [phase_for(i, 5) for i in range(5)]
    assert got == list(PHASES)
    assert phase_for(2, 3) == "residue"  # the last paragraph is always the residue


def test_register_never_persists_between_paragraphs():
    spec = compile_constraints(DENSE)
    seq = [register_for(spec, i) for i in range(8)]
    assert all(seq[i] != seq[i + 1] for i in range(len(seq) - 1))


def test_memory_field_contradicts_only_when_destabilized():
    stable = memory_note_for(WORLD, 0, "pressure", destabilize=False)
    unstable = memory_note_for(WORLD, 0, "pressure", destabilize=True)
    assert stable is not None and "exactly the state" in stable
    assert unstable is not None and "discrepancy" in unstable
    assert memory_note_for(WORLD, 0, "establishment", destabilize=False) is None


def test_objects_seen_matches_on_significant_words():
    assert objects_seen_in(WORLD, "The glass was warm.") == ["the glass"]
    assert objects_seen_in(WORLD, "Nothing here.") == []


# --- the loop -------------------------------------------------------------------------


def test_generate_runs_the_state_machine_over_paragraphs():
    client = _FakeClient()
    run = generate(dials=DENSE, situation="A man returns to a flat.",
                   paragraphs=5, client=client, model="m")
    assert len(run.paragraphs) == 5
    assert [p.phase for p in run.paragraphs] == list(PHASES)
    # state visibly evolves: energy rises to the breakdown, register rotates every step
    assert run.paragraphs[0].emotional_energy < run.paragraphs[3].emotional_energy
    regs = [p.language_register for p in run.paragraphs]
    assert all(regs[i] != regs[i + 1] for i in range(len(regs) - 1))
    # objects, not plot, carry continuity
    assert all("the glass" in p.objects_seen for p in run.paragraphs)
    assert any(p.memory_note for p in run.paragraphs)
    # one seeding call plus one render per paragraph — a loop, not a single prompt
    assert len(client.messages.parse_calls) == 1
    assert len(client.messages.create_calls) == 5


def test_generate_prompt_carries_rules_state_and_continuity():
    client = _FakeClient()
    generate(dials=DENSE, situation="A man returns to a flat.",
             paragraphs=2, client=client, model="m")
    first = client.messages.create_calls[0]["messages"][0]["content"]
    second = client.messages.create_calls[1]["messages"][0]["content"]
    assert "WORLD STATE" in first and "RULES" in first
    assert "Metaphor upon metaphor" in first  # compiled rule reached the renderer
    assert "PREVIOUS PARAGRAPH" not in first  # nothing to continue from yet
    assert "PREVIOUS PARAGRAPH" in second  # ...but the second continues the first


def test_generate_rejects_empty_situation_and_bad_counts():
    client = _FakeClient()
    with pytest.raises(EngineError):
        generate(dials=FLAT, situation="   ", paragraphs=3, client=client, model="m")
    with pytest.raises(EngineError):
        generate(dials=FLAT, situation="ok", paragraphs=0, client=client, model="m")
