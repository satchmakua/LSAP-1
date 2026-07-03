# LSAP-1 — Design

> One coordinate system for reading prose, one controllable engine for writing it —
> built as an honest instrument first, a generator second, with a hard wall between them.

**Status:** Design draft · **Language:** Python 3.12 (core) + TypeScript (UI) · **Stack target:** local-first desktop web app (FastAPI + React)

This document is the **engineering** design for LSAP-1. The *theory* — the L0–L7 stack,
the Epistemic Charter, the discipline substrate — lives in
[LSAP_Foundational_Blueprint.md](LSAP_Foundational_Blueprint.md) and is the source of
truth for *why* the system decomposes the way it does. This doc decides *how to build
it*: the stack, the exact data contracts, the module boundaries, and a runnable
milestone order. Where the two disagree, the blueprint wins on theory and this doc wins
on implementation. `ROADMAP.md` (produced by `/scaffold`) turns §8 into a build order.

> **Scope note.** v1 is the **full thin vertical slice** through the stack: *rate a
> passage (L1) → project it into coordinate space (L2/L3) → move a slider and generate
> differently (L6)*. The deep research layers — interpretation tensor (L4), archetype
> overlay (L5), multi-agent simulation (L7), and the combinatorial ideation combinator
> (Part V) — are **explicit v2+** (§2 non-goals). This honors both the blueprint's prime
> directive (it's a writing tool) and its honest-work ordering (build the instrument
> before the fun).

---

## 1. Concept

LSAP-1 is two instruments that share a vocabulary but **never share a wire**:

- **The Instrument** turns a prose segment into **30 anchored numbers** under a rigid,
  anti-interpretive protocol, then reduces those to a **5–6 dimension coordinate space**
  (the Literary Big Five: Compression, Narrative Structure, Consciousness Depth,
  Epistemic Stability, Affective Intensity, + a residual). Two raters — one Claude model,
  one human (or a second, cheaper Claude model) — run the *same* manual; the agreement
  between them is itself a validation signal, and their *disagreement* is a first-class
  output, not noise.
- **The Engine** takes five sliders and a set of *irreducible operators* (B1–B6 —
  Compression, Temporal Structure, Interiorization, (De)Stabilization, Affective
  Amplification, Agential Pressure) and compiles them into **generation rules**, then
  runs a **stateful cognition loop** (World State · Perception · Memory · Emotion ·
  Register) that renders prose sentence-by-sentence. Moving one slider produces *legibly*
  different prose across runs; state visibly evolves across paragraphs. It is a
  simulator, not a prompt.

A reader should be able to: paste a scene, watch it become 30 scores with per-axis
confidence, see it land as a dot in a 2-D projection of C-space next to its nearest
neighbors — then flip to the Engine Console, push "Compression" from low to high, and
watch the generated prose fold from plain declaratives into nested, metaphor-dense
clauses while the memory field makes a glass on a table quietly contradict itself.

### Engineering pillars (the 1–3 things that make or break this)

1. **Instrument reliability.** If two raters can't produce convergent 30-axis scores
   under the manual, nothing downstream is grounded and the "coordinate system" is
   decoration. The hard part is anchored scales + forced-choice discipline + confidence
   scoring + structured LLM output that resists interpretive drift. **This is measured,
   not asserted** (M2 computes real inter-rater numbers).
2. **The firewall (Charter Principle 4).** The model that *reads* (`instrument/`,
   `coordinates/`) and the model that *writes* (`engine/`) must be **architecturally
   incapable of feeding each other**. If generation reuses the analysis model, the system
   drifts into self-confirming caricature. We enforce this as a **code invariant**, not a
   guideline (§4, §5).
3. **The constraint compiler + runtime cognition.** Turning a slider into *rules*
   ("nested clauses allowed, metaphor stacking, implicit meaning encouraged") rather than
   a *description* ("be dense"), and running a stateful WS/PL/MF/EF/LR loop that makes the
   difference between a simulator and a fancy prompt.

---

## 2. Goals / Non-goals

**Goals (v1 must achieve):**
- Turn an arbitrary ~1–3k-word segment into a validated 30-axis rating with per-axis
  confidence, reproducibly, via a Claude rater under a frozen manual.
- Assemble a 30-segment pilot corpus (with deliberate redundant pairs) and report, **with
  numbers**, inter-rater agreement, the axis correlation matrix, and the emergent latent
  factors (PCA) — including which axes are reliable, redundant, or ambiguous.
- Project any new segment into the fitted C-space and surface nearest neighbors that a
  human finds intuitively sensible.
- Generate prose from five sliders such that moving **one** slider produces a *legibly
  different* prose behavior, and world-state visibly evolves across paragraphs.
- Keep the analysis path and the generation path provably disconnected (an automated test
  fails if `engine/` imports the instrument).

**Non-goals (explicitly out of v1 — the guardrails that keep the build on track):**
- **No authorship attribution.** LSAP-1 is *not* stylometry-for-detection (Burrows'
  Delta, "who wrote this", AI-text detectors). Named authors are analysis waypoints, never
  targets or basis vectors (Charter P7). This is the sharpest line separating us from the
  existing field.
- **No claim of ground-truth coordinates.** Reliability means *consistent projection
  under a protocol*, not objective correctness (Charter P1). Anything claiming more has
  left the charter.
- **No L4 interpretation tensor, L5 archetype/phase-transition classifier, or L7
  multi-agent simulation** in v1. These are the highest-risk research layers; v1 builds
  the vertical slice they will later sit on.
- **No Work-Description combinator (D3)** in v1 — it's orthogonal to the stack and a clean
  fast-follow, but out of the core slice.
- **No fine-tuning / no custom model training.** Claude-as-rater and Claude-as-renderer
  only.
- **No multi-user, auth, accounts, or cloud hosting.** Single-user, local-first,
  file-based, git-diffable data. No database server.
- **No general writing IDE.** It's an instrument + engine, not a Scrivener replacement.
- **No mobile app, no real-time collaboration.**

---

## 3. Tech stack

Versions verified 2026-07-02.

| Layer | Choice | Why |
|---|---|---|
| Core language | **Python 3.12** | The instrument (PCA/reliability stats) and the engine (LLM orchestration, stateful loop) share one language and one repo; best-in-class data-science + LLM ecosystem. |
| Env / package manager | **uv 0.11.x** | One Rust-fast tool for venv + deps + Python version; 10–100× pip. Right for a fast solo loop. |
| Backend API | **FastAPI + Uvicorn** | Typed, async, Pydantic-native; exposes rater / projection / engine as endpoints the UI calls, with SSE for streamed generation. |
| Data models / validation | **Pydantic v2 (≥2.11)** | The rating schema *is* the contract. Pydantic enforces it **and** drives Claude structured output (`messages.parse`) so the 30-axis result can't come back malformed. |
| LLM | **Claude via `anthropic` SDK** — `claude-opus-4-8` (canonical rater + renderer), `claude-haiku-4-5` (cheap second rater) | Latest capable models. Structured outputs force the axis schema; adaptive thinking for the rater's judgment task; streaming for the engine. |
| Stats / reduction | **scikit-learn + numpy + pandas** | Standard PCA, correlation matrices, inter-rater agreement (Krippendorff / weighted κ). Notebook-friendly for the reliability run. |
| Frontend | **React 19 + TypeScript + Vite 8** | Fast HMR; the Rater Studio, Engine Console, and C-Space map are genuinely interactive. (create-vite scaffolds React 18 — upgrade to 19 explicitly.) |
| UI kit | **Tailwind + shadcn/ui** | Clean, legible instrument UI fast, no bespoke design system. |
| Client state | **Zustand** | Light store for slider state + streamed tokens; no Redux ceremony. |
| C-space viz | **Recharts** for standard scatter/bars; **SVG + `d3-scale`** for C-space trajectories | Recharts gets the pilot plots fast; trajectory rendering (paths through C-space) drops to hand-rolled SVG for control. |
| Persistence | **Local files** — `corpus/*.md` (frontmatter), `*.yaml` (axis/operator defs), `*.jsonl` (ratings), `coordinates/model.json` (fitted PCA) | Git-diffable, inspectable, matches the markdown-everywhere workflow. **No DB server** in v1. |
| Testing | **pytest** (backend) + **Vitest** (frontend) | Standard, fast; includes the firewall-import test. |

**The library doing the heavy lifting:** the `anthropic` SDK's **structured outputs**.
The entire instrument depends on getting a strict, schema-valid 30-axis object back every
time; `messages.parse` against a Pydantic model makes that a guarantee rather than a
parsing exercise. Consult the `claude-api` skill for current model IDs and the
`output_config.format` / adaptive-thinking specifics before wiring the rater.

---

## 4. The measurement & coordinate core — get this exactly right

Everything hinges on two contracts: the **rating record** (30 axes, anchored, with
confidence) and the **projection** (30 axes → C-space via PCA). Get these exact and the
reliability analysis, the map, and the firewall all have something precise to stand on.

### 4.1 The instrument (L1) — data-driven axis registry + rating schema

Axes are **data, not code** (`instrument/axes.yaml`), so tuning the instrument is a data
change, never a rewrite. A segment is a coherent scene unit, **~1,000–3,000 words**. Each
scalar axis is a **7-point anchored** scale; two axes are forced-choice.

```python
# instrument/schema.py — the measurement contract (Pydantic v2)
from typing import Literal
from pydantic import BaseModel, conint

Field = Literal["L", "N", "C", "P", "A", "S"]  # Language / Narrative / Consciousness /
                                               # Philosophy / Affective / Stylistic

class AxisDef(BaseModel):          # loaded from instrument/axes.yaml
    id: str                        # "L1","N3","A3",... (30 total, 5 per field)
    field: Field
    name: str                      # "Lexical Complexity"
    kind: Literal["scalar", "forced_choice"]
    anchors: dict[int, str] | None # {1:"...",4:"...",7:"..."} for scalar axes
    choices: list[str] | None      # forced-choice options (A3, S5)
    definition: str                # what is present, NOT whether it's good
    watch_for: list[str]           # contamination warnings (genre, semantic leakage, ...)

class AxisScore(BaseModel):
    axis_id: str
    value: conint(ge=1, le=7)      # 7-pt scalar, OR 1-based index into choices
    confidence: conint(ge=1, le=5) # 1 guessing .. 5 very high

class Rating(BaseModel):
    segment_id: str
    rater_id: str                  # "claude-opus-4-8" | "claude-haiku-4-5" | "human:sh"
    scores: list[AxisScore]        # exactly 30, in fixed field order L→N→C→P→A→S
    flagged: bool                  # True if confidence<=2 on >40% of axes -> review
    created_at: str                # ISO 8601, injected by caller (no wall-clock in pure code)
```

The 30 axes (blueprint §6), five per field:
- **L** Lexical Complexity · Syntactic Depth · Semantic Density · Imagery Mode · Repetition Pattern
- **N** Event Density · Structural Linearity · Causal Clarity · Temporal Behavior · Plot Centrality
- **C** Narrative Distance · Subject Stability · Cognitive Transparency · Polyphony · Interior/Exterior Ratio
- **P** Ontological Stability · Epistemic Certainty · Moral-Structure Clarity · Meaning Structure · Agency Model
- **A** Valence · Emotional Volatility · **Dominant Affect** *(forced choice: awe/dread/grief/joy/curiosity/horror/alienation/absurdity)* · Intensity Curve · Resolution Type
- **S** Rhythm Regularity · Sentence-Length Variance · Voice Dominance · Figurative Density · **Aesthetic Register** *(forced choice: documentary/poetic/surreal/experimental)*

Anchor example (concrete numbers matter — this is what makes it reproducible):

```yaml
# instrument/axes.yaml (excerpt)
- id: N1
  field: N
  name: Event Density
  kind: scalar
  definition: How many discrete state-changing events occur per unit text. Score behavior, not importance.
  anchors:
    1: "Near-static; almost no events (a description, a reverie)."
    4: "Steady incident; events arrive at a walking pace."
    7: "Relentless; multiple state-changes per paragraph."
  watch_for: ["Do not confuse event density with pace of prose", "A long sentence can hold many events"]
```

**Rater discipline** (from the manual, enforced in the rater prompt): no literary
judgment ("what is present?", never "is this good?"); score behavior not meaning; ignore
author identity and genre reputation; no cross-axis contamination; four-pass workflow
(read → mark structure → score in fixed order → score confidence). The rater returns a
`Rating` via structured output; the harness computes `flagged`.

### 4.2 The projection (L2/L3) — 30 axes → C-space

The 30 features are the *instrument*, not the coordinate system. Fit **PCA** over enough
ratings and they collapse to ~5–6 latent factors. This is the moment the framework either
crystallizes or reveals a more interesting shape — **either outcome passes** (Charter P3).

```python
# coordinates/projection.py — 30 anchored axes --PCA--> C in [0,1]^5 (+ residual)
# scalar axes normalized (value-1)/6 -> [0,1]; forced-choice one-hot before PCA.
from pydantic import BaseModel

class CVector(BaseModel):
    c1_compression: float            # semantic density, metaphor load, condensation, rhythm
    c2_narrative_structure: float    # linearity <-> fragmentation; causality; time
    c3_consciousness_depth: float    # interiority, POV immersion, subject coherence
    c4_epistemic_stability: float    # consistency <-> paradox of reality-rules
    c5_affective_intensity: float    # emotional volatility, tonal amplitude
    c6_residual: float               # the acknowledged remainder (Charter P5)

class ProjectionModel:
    def fit(self, ratings: list[Rating]) -> None: ...      # sklearn PCA over the corpus
    def project(self, rating: Rating) -> CVector: ...      # a single point in C-space
    def explained_variance(self) -> list[float]: ...       # per-factor variance explained
    # persisted to coordinates/model.json so the map + engine-eval are reproducible
```

Canonical names (blueprint §16 glossary) are used **everywhere downstream**; the glossary
is the single source of truth when this doc and the blueprint drift on naming.

### 4.3 The firewall invariant (Charter Principle 4) — a structural, tested rule

```
INVARIANT:  engine/  MUST NOT import from  instrument/  or  coordinates/projection/.
```

The engine generates from the **operator basis + constraint compiler**, never from
measured coordinate regions. The engine's sliders are named C1–C5 *for the writer's
intuition*, but they are **control inputs to operators B1–B5**, computed by a path with
**zero dependency** on the instrument's fitted PCA. Generated prose *may* be evaluated by
re-rating it through the instrument (allowed, and how we measure "legibly different"), but
that measurement **never feeds back into generation**. A pytest scans `engine/`'s import
graph and fails the build on violation.

---

## 5. Architecture

Structural pattern: **ports-and-adapters with a hard directional rule**, organized as a
Python monorepo package tree that mirrors the blueprint's repo layout — three *spaces*
that stay distinct (generative / interpretation / label), with a React SPA on top talking
to a thin FastAPI layer.

```
                          React SPA (Vite)
        ┌───────────────┬───────────────┬────────────────┐
        │ Rater Studio  │ C-Space Map   │ Engine Console │   ← three surfaces
        └───────┬───────┴───────┬───────┴────────┬───────┘
                │ REST          │ REST           │ SSE (streamed prose)
        ┌───────▼───────────────▼────────────────▼───────┐
        │                 FastAPI (api/)                  │
        └───────┬───────────────┬────────────────┬───────┘
                │               │                │
      ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼────────────┐
      │  instrument/   │ │ coordinates/ │ │     engine/       │
      │  (L1 rater)    │ │ (L2/L3 PCA,  │ │ (L6: operators,   │
      │                │ │  projection, │ │  constraint       │
      │  axes.yaml     │ │  C-space map)│ │  compiler,        │
      │  schema.py     │ │              │ │  runtime cognition│
      │  rater.py      │ │              │ │  WS·PL·MF·EF·LR)  │
      └───────┬────────┘ └──────┬───────┘ └──────┬────────────┘
              │                 │                 │
              ▼                 ▼                 ▼
      corpus/*.md        coordinates/model.json   engine/presets/*.yaml
      ratings/*.jsonl                             operators.yaml

        interpretation space │ label space │ GENERATIVE space
        ───────────────────────────────────────────────────
        FIREWALL: no import arrow from engine/ back into instrument/ or coordinates/
        (analysis reads text; generation writes it; they meet only in the UI and in
         an offline eval that re-rates engine output)
```

- **`instrument/`** — the L1 rater: loads `axes.yaml`, prompts Claude under the manual,
  returns a validated `Rating`, persists to `ratings/*.jsonl`. Pure interpretation space.
- **`coordinates/`** — L2/L3: fits and applies PCA, serves projections and nearest
  neighbors, produces the C-space map data. Label space. Depends on `instrument/` schema
  (read-only), never the reverse.
- **`engine/`** — L6: operators (`operators.yaml`), the constraint compiler, the story
  state machine, and the runtime cognition subsystems. Generative space. **Imports
  nothing from the other two.**
- **`api/`** — FastAPI adapters; the *only* place the three packages are wired to the same
  process, and even there they don't call each other.

---

## 6. Core systems

### 6.1 The rater (`instrument/rater.py`)

Prompts Claude with the frozen manual + the target segment, forces a `Rating` via
structured output, computes `flagged`. Opus 4.8 is the canonical rater with adaptive
thinking on (it's a judgment task); Haiku 4.5 is the cheap second rater for convergence.

```python
def rate(segment: str, rater: str, axes: list[AxisDef]) -> Rating: ...
# uses client.messages.parse(..., output_config={"format": <Rating schema>})
# manual + axes serialized into the system prompt; segment in the user turn.
```

### 6.2 Reliability (`coordinates/reliability.py`)

Over the rated corpus: inter-rater agreement per axis (weighted κ / Krippendorff's α on
ordinal axes; exact-match rate on forced-choice), the 30×30 axis correlation matrix, and
the PCA fit. Output is a report (numbers + a notebook) that answers: which axes are
reliable, which are redundant (merge), which are ambiguous (redesign), and what the latent
structure is.

### 6.3 The engine (`engine/`)

The pipeline, and the runtime cognition contract:

```python
# engine/compiler.py — dials -> RULES (not descriptions).  Imports nothing from instrument/.
from typing import Literal
from pydantic import BaseModel

Band = Literal["low", "med", "high", "extreme"]

class Dials(BaseModel):              # the ONLY input the UI sends the engine
    c1: float; c2: float; c3: float; c4: float; c5: float   # slider values in [0,1]
    style_seed: str | None = None

def to_bands(d: Dials) -> dict[str, Band]: ...              # normalize to control bands
def compile_constraints(bands: dict[str, Band]) -> "ConstraintSpec": ...
# e.g. c1=high -> {"clauses":"nested allowed","metaphor":"stacking","meaning":"implicit"}

# engine/runtime.py — the Style Engine: a scene resolved from 5 stateful subsystems
class WorldState(BaseModel):         # WS: ground truth
    facts: list[str]                 # 3..7 concrete; >=2 physical objects; no emotion
    time_pos: int
class RuntimeState(BaseModel):
    ws: WorldState
    emotional_energy: float          # EF 0..5 (physics of attention)
    register: str                    # LR: rotates; no register persists > 2 sentences
    memory: list[str]                # MF: prior object-states, misremembered facts
    unresolved: list[str]            # objects carry continuity, not plot

def step(state: RuntimeState, spec: "ConstraintSpec") -> tuple[str, RuntimeState]: ...
# renders the next sentence(s) via Claude (streamed), then updates state -> the feedback
# loop that makes it a simulator. Scene follows 5 phases: Establishment -> Drift ->
# Pressure -> Breakdown -> Residue (ends on an unresolved object state).
```

Presets (`engine/presets/*.yaml`) are dial-a-configuration starting points — the project's
own house style (Realism + Sebald + Expressionism primary) can live here as one preset.
Sensible defaults so the tool never paralyzes the writer (Charter P9).

---

## 7. UX / interface

Three surfaces, one feel-good loop each. Local web app, single window, tabbed.

- **Rater Studio** — paste/select a segment → "Rate" → the 30 axes render as a grouped
  bar/heat strip colored by **confidence**, forced-choice axes as chips, low-confidence
  axes flagged. Side-by-side column when a second rater exists, with agreement highlighted.
  *The loop:* watch a passage become legible numbers.
- **C-Space Map** — a 2-D projection (choose which two C-axes, or PCA-2D) scatter of the
  corpus; the current segment is a highlighted dot with its nearest neighbors labeled;
  optional trajectory line for a multi-segment work. *The loop:* "where does this sit, and
  what's near it?"
- **Engine Console** — five labeled sliders (Compression, Narrative Structure,
  Consciousness Depth, Epistemic Stability, Affective Intensity) + a preset picker →
  "Generate" streams prose token-by-token while a **state panel** shows WS objects, EF
  level, and the current register updating per paragraph. A "re-rate this output" button
  runs it back through the Instrument (the *only* sanctioned crossing, and it's one-way,
  offline of generation). *The loop:* move one slider, watch the prose change character.

---

## 8. Milestones

Independently-runnable, top-down. M0 is the walking skeleton; each later milestone deepens
the same vertical slice and demonstrates something a human can test.

- **M0 — Skeleton & it runs.** uv-managed Python backend (FastAPI health route) + Vite
  React 19 app that loads and fetches it; one `AxisDef` parsed from `axes.yaml` and
  rendered; pytest + Vitest each green; the **firewall import-test stub** in place.
  *Demonstrates:* the whole toolchain runs end-to-end and the wall exists from day one.
- **M1 — Instrument, one segment end-to-end.** Full 30-axis `axes.yaml`, the `Rating`
  schema, a Claude rater returning structured output, persistence to `ratings/*.jsonl`,
  Rater Studio showing scores + confidence. *Demonstrates:* a passage becomes 30
  reproducible numbers.
- **M2 — Pilot corpus + reliability.** The 30-segment corpus (with redundant pairs) under
  `corpus/`; both raters (Opus + Haiku) run; inter-rater agreement, the correlation
  matrix, and a first PCA reported with real numbers. *Demonstrates:* the honest question —
  does the instrument converge? — answered with data (either answer passes).
- **M3 — Coordinate system v1.** Lock the surviving Big Five (+ residual); fit and persist
  the PCA; project an arbitrary new segment; C-Space Map with nearest neighbors and a
  trajectory. *Demonstrates:* a new segment lands somewhere a human finds sensible.
- **M4 — Generative Engine MVP.** `operators.yaml`, band-normalizer, constraint compiler,
  story state machine, runtime cognition (WS/PL/MF/EF/LR), streamed generation, presets,
  Engine Console + state panel; the "re-rate output" crossing. *Demonstrates:* moving one
  slider yields legibly different prose across runs; state visibly evolves — a simulator,
  not a prompt.

*v2+ (not in this slice):* L4 interpretation tensor · L5 archetype/phase-transition
classifier · L7 multi-agent simulation · the Work-Description combinator (D3).

---

## 9. Risks / open questions

- **The instrument may not converge** (raters disagree widely). → Per the Charter this is
  *data, not failure* (P2): high-variance axes are diagnostic. M2 tells us which axes to
  merge or redesign; the framework is allowed to "reveal a more interesting shape."
- **LLM rater drift / non-determinism.** → Structured outputs + a frozen manual + explicit
  confidence + running each rating N times and reporting spread. Determinism isn't the
  goal; *measured consistency* is.
- **Accidental firewall violation** (the subtlest, highest-cost risk). → Package
  boundaries + an automated import test in M0; the "re-rate output" path is offline of
  generation by construction.
- **The engine produces mush** (Claude smooths the sliders into generic "literary" prose).
  → Compiler emits *rules* not adjectives; stateful loop with register rotation and object
  memory; and we *measure* differentness by re-rating generated output (Charter-clean,
  since it never loops back into generation).
- **Scope creep up the stack.** → v1 hard-stops at M4; L4/L5/L7 are non-goals with a clean
  seam to add later.
- **Open question:** which inter-rater metric is primary for mixed ordinal + nominal axes
  (Krippendorff's α with per-axis distance functions vs. per-field weighted κ)? Resolve in
  M2 against real data rather than deciding blind now.

---

## 10. References

- **[LSAP_Foundational_Blueprint.md](LSAP_Foundational_Blueprint.md)** — the canonical
  theory (L0–L7 stack, Epistemic Charter, glossary). This design implements Phases 1–4 of
  its roadmap.
- **Prior art / the niche** (verified 2026-07-02): existing computational tools — **Stylo**
  (R), **JGAAP**, **LIWC**, **StyloMetrix**, and metrics like **Burrows' Delta** — are
  built for *authorship attribution and classification* via function-word frequencies.
  LSAP-1 deliberately targets a different niche: a *semantic/structural coordinate system
  for generation with interpretive variance as a first-class output*. StyloMetrix (open
  stylometric feature vectors) is the closest analog to the L1 feature layer; the Nature
  2025 study on human-vs-AI creative-writing stylometry underlines why the analysis↔
  generation firewall matters.
- **Stack docs** (verify current APIs before use): FastAPI + Pydantic v2, scikit-learn
  (PCA), `anthropic` Python SDK (see the `claude-api` skill for model IDs / structured
  outputs / adaptive thinking), Vite + React 19, uv.
- **Reuse across your projects:** the local-first, markdown/YAML/JSONL, git-diffable data
  posture and the phase-gated `ROADMAP`/`PROGRESS` workflow match the conventions in your
  `_TEMPLATE` and sibling projects.
