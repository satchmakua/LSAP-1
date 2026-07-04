# LSAP — Foundational Blueprint

### The Literary Space Annotation Protocol & The Unified Theory of Literature

*A layered system for measuring, mapping, and generating prose. One coordinate system for possible literature; one honest instrument for reading it; one controllable engine for writing it.*

**Status:** Foundation (v0.1) — this document supersedes the draft notes and is the canonical reference.
**Format:** Git-diffable Markdown. This file is the root; everything downstream inherits its definitions.

---

## 0. What this document is

You have three sprawling draft files — hundreds of iterations run through various models. They contain a real idea buried under heavy redundancy, several genuinely sharp self-critiques, and a lot of the same insight restated in slightly different words. This blueprint keeps the ore and discards the chaff. It does three things:

1. **Names the single unifying architecture** that the drafts were circling but never stated cleanly (Part I).
2. **Fixes the epistemology** — the drafts oscillate between "this is a science of literature" and "no it isn't." That oscillation is resolved here by assigning *different truth-claims to different layers* (the Epistemic Charter, §3).
3. **Gives you a buildable path** — phase-gated, with explicit exit criteria and a repository structure you can hand to Claude Code (Part VI).

Read Part I to understand the whole. Read Parts II–V for each layer's spec. Read Part VI to build.

---

# PART I — ORIENTATION

## 1. The program in one page

**Mission.** Build a *language for thinking about storytelling* that is rigorous enough to measure with and expressive enough to write with. Life is largely the stories we tell ourselves and each other; the goal is an instrument for that, not a replacement for it.

**LSAP** (Literary Space Annotation Protocol) is the umbrella program. Under it sit three deliverables:

- **D1 — A Unified Theory of Literature (UTL).** A descriptive account of what prose is made of, grounded in the disciplines that actually govern it (linguistics, cognition, systems, information, culture, meaning, experience).
- **D2 — A storytelling engine and tool.** A controllable system that generates prose by dialing structural parameters, not by imitating named authors.
- **D3 — A combinatorial ideation system.** A way to combine genres, tones, and setting-aesthetics along independent axes to invent prose and premises that don't yet exist.

**The relationship between UTL and LSAP-1** (the thing the drafts never made explicit):

> **UTL is the theory. LSAP-1 is the instrument.** UTL says *why* literary structure decomposes the way it does — because writing is a communication-and-cognition system inheriting laws from other fields. LSAP-1 is the reproducible protocol that *measures* that decomposition and turns it into a coordinate system. They are two ends of one program: substrate and ruler. Neither is complete without the other. This document holds both.

**The prime directive.** The system's first and highest purpose is to be an excellent tool for *story creation, ideation, and writing*. Every other property — the math, the measurement, the taxonomy — is in service of that. When a design choice trades away creative usefulness for the appearance of rigor, the creative usefulness wins.

---

## 2. The central idea — the Layered Stack

The drafts contain at least four different "final architectures" that all describe the same thing at different zoom levels. Unified, they form a single vertical stack. Each layer is a distinct object with a distinct job and — critically — a distinct *epistemic status* (how much we're allowed to believe it corresponds to something real).

```
                        THE LSAP STACK
   ┌──────────────────────────────────────────────────────────────┐
   │  L7  MULTI-AGENT SIMULATION                    creation (world) │
   │      Writers as competing force-laws over a shared world.      │
   ├──────────────────────────────────────────────────────────────┤
   │  L6  GENERATIVE ENGINE                         creation (voice) │
   │      Sliders → constraint compiler → stateful runtime cognition.│
   ├──────────────────────────────────────────────────────────────┤
   │  L5  ARCHETYPE / SYMBOLIC OVERLAY              compression      │
   │      Attractor basins + phase-transition names (tarot/I-Ching). │
   ├──────────────────────────────────────────────────────────────┤
   │  L4  INTERPRETATION TENSOR                     epistemics       │
   │      Reader-dependent probability distributions. Disagreement.  │
   ├──────────────────────────────────────────────────────────────┤
   │  L3  OPERATOR BASIS — NARRATIVE PHYSICS        generative moves │
   │      B1–B6: the irreducible transformations of prose.          │
   ├──────────────────────────────────────────────────────────────┤
   │  L2  LATENT COORDINATE SPACE — LITERARY BIG 5  instrumentation  │
   │      C1–C5 (+ residual). Frame-dependent, useful, not "truth."  │
   ├──────────────────────────────────────────────────────────────┤
   │  L1  OBSERVABLE-FEATURE INSTRUMENT             measurement      │
   │      30 anchored axes across 6 fields. Reproducible rating.     │
   ├──────────────────────────────────────────────────────────────┤
   │  L0  TRANS-DISCIPLINARY SUBSTRATE (UTL)        foundation       │
   │      Why the axes exist. Writing as inherited system laws.      │
   └──────────────────────────────────────────────────────────────┘

     Orthogonal to the stack:  WORK-DESCRIPTION SPACE (Part V)
     Independent descriptive dimensions — genre, tone, theme,
     structure, philosophy, emotional & stylistic signature,
     setting-aesthetic paradigm ("punk" frameworks). These label
     a work; they are not layers of it.
```

**How to read the stack.** Information flows *up* when generating (choose operators → render voice → simulate a world) and *down* when analyzing (observe features → project into coordinates → recognize an archetype). The two directions are deliberately **not** the same pipeline; conflating them is a named failure mode (§3, Principle 4).

**The single most important structural fact:** the stack separates three things the drafts constantly smear together —

- **Generative space** (what produces text): L3 operators + L6 runtime.
- **Interpretation space** (how it's read): L1 features + L4 tensor.
- **Label space** (how we describe it): L2 coordinates, L5 archetypes, Part V descriptors.

Labels like "Kafka-like" are *post-hoc compressions of a region in generative space*, never system primitives. Keep these three spaces distinct and most of the drafts' contradictions dissolve.

---

## 3. The Epistemic Charter

This is the honesty spine of the project — the distilled lessons from every "critical view" and "weaknesses" section in the drafts. These are not optional caveats; they are *load-bearing design constraints*. A version of this system that ignores them becomes what the drafts correctly feared: a convincing simulation of rigor with nothing underneath.

**Principle 1 — Instrumentation, not ontology.** We are not discovering the true coordinates of literature. We are building a lens that reveals certain structures more clearly than others. The right analogy is a color space (RGB vs. LAB) or a coordinate frame in physics (Cartesian vs. polar): none is "truth," some are extremely useful. Reliability means *consistent projection under a defined protocol*, not objective correctness.

**Principle 2 — Disagreement is signal, not error.** Two readers scoring a passage differently is data about the passage, not noise to be averaged away. Interpretive variance is a *measurable property of literary structure* and is treated as a first-class output (this is what L4, the tensor, exists for). High-variance passages are often the interesting ones.

**Principle 3 — The axes are entangled; model it.** The Big Five are *not* cleanly independent. Compression touches rhythm; consciousness touches epistemic stability; affect reshapes perceived structure. What actually exists is an entangled manifold, not a tidy orthogonal grid. Never assume separability; expect the "five" to sometimes collapse toward two or three real factors, and design for coupling rather than pretending it away. (A "manifold" here = a space that is only locally grid-like; a "basis" that works in one genre may need rotating for another.)

**Principle 4 — Separate the descriptive model from the generative model.** The instrument that *reads* text (L1/L2) and the engine that *writes* it (L6) must not be the same object. If generation reuses the analysis model directly, you get a self-confirming loop: "Hemingway-ish" output strengthens the "Hemingway region," which produces more caricatured "Hemingway-ish" output. The system drifts toward stylized caricature and away from real literature. Keep a firewall.

**Principle 5 — Keep a residual axis for the un-capturable.** Explicitly reserve a dimension for what the model *cannot* represent: irony, cultural subtext, historical resonance, intertextuality, genre-expectation subversion, and meaning-through-omission. Naming the residual is what stops the model from silently claiming to be complete. Mapping is always lossy; the residual is where we admit it.

**Principle 6 — Archetypes summarize; they never define.** The symbolic layer (L5) is a compression tool, a human-readable coordinate landmark. The moment "The Tower appeared" starts *explaining* the text instead of *summarizing* a measured state, it has become decoration and must be pulled back. Symbolic overfitting — seeing a "Borges collapse" in ordinary variance — is a real and seductive failure.

**Principle 7 — Named authors are samples, not basis vectors.** Woolf, Borges, Kafka, Hemingway are convenient attractor points we already have cultural names for. They are *corpora, not agents* — internally inconsistent, context-sensitive, non-stationary. The system must be able to *generate* authorial regions, not merely imitate four of them. Treating a writer as a fixed behavioral law produces brittle "literary caricature physics."

**Principle 8 — The best literature resists the axes.** Great writing is frequently a *process of destabilizing* the reader's state models, not a stable point that sits neatly in the grid. Accept the paradox: the instrument may work most cleanly on mediocre prose and strain against the greatest. That strain is diagnostic, not a bug to be engineered out.

**Principle 9 — Instrument the writer, don't imprison them.** Too many dials cause paralysis-by-analysis and kill intuitive flow. The tool must *enhance* creativity, not over-instrument it. Sensible defaults, presets, and the ability to ignore the whole apparatus are features, not conveniences.

---

## 4. Non-goals

LSAP explicitly does **not** claim:

- objective ground-truth values for literature;
- full capture of meaning, culture, or historical context;
- elimination of interpretive plurality (it *encodes* plurality — see L4);
- reduction of literature to deterministic coordinates.

It is strictly a *structured, probabilistic framework for representing and generating prose under acknowledged uncertainty.* Anything claiming more than that has left the charter.

---

# PART II — THE THEORY (UTL)

## 5. Layer 0 — The trans-disciplinary substrate

**Why this layer exists.** The Big Five axes are not arbitrary. They fall out of the fact that *writing is a communication-and-cognition system*, and such systems inherit laws from the disciplines that study them. L0 is the answer to "why *these* dimensions?" — they are the literary shadows of deeper fields. This is UTL's core claim: stop treating writing as "words on paper" and treat it as a system, and the relevant sciences explode into view.

**The discipline hierarchy.** Six levels, from the medium up to the experience:

- **Level 1 — Language.** Linguistics, grammar, rhetoric, stylistics. *How does the medium itself work?*
- **Level 2 — Mind.** Cognitive, emotional, and social psychology; neuroscience. *What do readers notice, forget, fear, want?* (Suspense is prediction management; comedy is violated prediction; horror exploits threat-and-uncertainty processing.)
- **Level 3 — Systems.** Software engineering, information theory, cybernetics, systems theory. *A novel is a stateful system; characters hold beliefs, goals, knowledge, emotion; scenes are state transitions.* Narrative tension can be read as *desired information minus available information* (Shannon).
- **Level 4 — Humans.** Anthropology, sociology, history, economics, game theory. *How do cultures, institutions, incentives, and conflicts actually behave?* The difference between a setting and a culture is anthropology; believable intrigue is game theory.
- **Level 5 — Meaning.** Philosophy, religion, ethics. *What is identity, personhood, morality?* Enduring novels are often philosophical investigations disguised as stories.
- **Level 6 — Experience.** Music, architecture, design, cinema. *How does a person move through the work?* Sentence cadence is closer to music than to grammar; a chapter is a user experience; a novel is an interaction sequence.

**Language as the base control surface.** Because Level 1 is where the writer's hands actually touch the material, it gets special treatment. Behind ordinary grammar sit three layers the drafts identify clearly:

1. **Structure** — syntax, morphology (how sentences and words are built).
2. **Meaning** — semantics, pragmatics (what is literally encoded vs. what is implied; pragmatics is where subtext lives).
3. **Effect** — stylistics, rhetoric, discourse (how choices create voice, tone, and impact). *If a writer studies one field, it is stylistics.*

Two operational insights from L0 that feed directly upward into the engine:

- **Words are roles, not fixed categories.** English is role-based: the sentence assigns a word its job ("run," "light," "exercise" shift between noun/verb/adjective by context — *functional shift*). This matters because **nouns feel heavier, more static, more abstract; verbs feel kinetic, immediate, narrative-driven** ("we had a discussion" vs. "we discussed it" — same meaning, different energy). Noun-heavy vs. verb-heavy prose is a *compression and tempo* control — i.e., it feeds C1 and C5 below.
- **Every mechanical part is an "engine."** Nouns anchor reality, verbs drive motion in time, adjectives/adverbs are the description and modulation layers, prepositions and conjunctions are the relationship and logic layers, articles control definiteness (how specific reality is in the reader's mind). Punctuation is *rhythm control*, not decoration.

A full grammar-and-craft curriculum (parts of speech → clause architecture → syntax variation → paragraph architecture → style synthesis) is a legitimate sub-module of L0 but is *pedagogy*, not foundation; it lives as its own document (`docs/craft-primer.md`) rather than in this blueprint.

---

# PART III — THE INSTRUMENT & COORDINATE SYSTEM (LSAP)

## 6. Layer 1 — The observable-feature instrument

This is the empirical base of the whole stack: a reproducible protocol for turning a prose segment into numbers *without interpreting its meaning*. It is deliberately rigid, slightly uncomfortable, and anti-interpretive — because interpretive freedom is precisely what destroys measurement systems.

**The 30 axes, across six fields.** Each axis is a concrete, observable feature scored on a **7-point anchored scale**. A segment is a coherent scene unit, typically ~1,000–3,000 words.

- **Language Field (L):** L1 Lexical Complexity · L2 Syntactic Depth · L3 Semantic Density (ideas per sentence, *not* length) · L4 Imagery Mode (concrete↔abstract) · L5 Repetition Pattern.
- **Narrative Field (N):** N1 Event Density · N2 Structural Linearity · N3 Causal Clarity · N4 Temporal Behavior · N5 Plot Centrality (*what happens* vs. *how it's experienced*).
- **Consciousness Field (C):** C1 Narrative Distance · C2 Subject Stability · C3 Cognitive Transparency · C4 Polyphony (active voices) · C5 Interior/Exterior Ratio.
- **Philosophy Field (P):** P1 Ontological Stability · P2 Epistemic Certainty · P3 Moral-Structure Clarity · P4 Meaning Structure · P5 Agency Model (free will↔determinism).
- **Affective Field (A):** A1 Valence (positive↔negative baseline) · A2 Emotional Volatility · A3 Dominant Affect (*forced choice:* awe/dread/grief/joy/curiosity/horror/alienation/absurdity) · A4 Intensity Curve · A5 Resolution Type (cathartic/unresolved/deflationary/collapse).
- **Stylistic Field (S):** S1 Rhythm Regularity · S2 Sentence-Length Variance · S3 Voice Dominance · S4 Figurative Density · S5 Aesthetic Register (*forced choice:* documentary/poetic/surreal/experimental).

**Rater discipline (distilled to the essentials).**

- **Golden rules:** no literary judgment (never "is this good?", only "what is present?"); score behavior, not meaning; ignore author identity and genre reputation; no cross-axis contamination.
- **Four-pass workflow:** (1) read only; (2) mark structure — sentence/dialogue/POV/time/emotion boundaries; (3) score axes in fixed order; (4) score *confidence* per axis (1 guessing → 5 very high). If confidence ≤2 on >40% of axes, flag the segment for review.
- **Disagreement protocol:** check definition-adherence first; if still divergent, mark the axis AMBIGUOUS; if an axis is repeatedly ambiguous across the corpus, it needs redesign or splitting.
- **Watch for:** literary-intuition drift (judging beauty), genre contamination ("Hemingway = low everything"), semantic leakage (theme mistaken for feature), and axis-merging (treating syntax + rhythm + tone as one thing).

Both trained humans and LLM raters run the identical manual; convergence between them is itself a validation signal.

---

## 7. Layer 2 — The latent coordinate space (the Literary Big Five)

The 30 features are the instrument; they are *not* the coordinate system. When you run dimensionality reduction over enough rated segments, the 30 axes collapse into roughly **five-to-six latent factors** — the recurring directions that explain most of the variation between texts. (This reduction is done with **PCA — Principal Component Analysis**, a standard statistical method that finds the few underlying dimensions accounting for the bulk of variation in a larger set of measurements.) In the drafts' pilot analysis these emerged as, in descending order of variance explained:

| Axis | Canonical name | What it captures | Aliases in drafts |
|------|----------------|------------------|--------------------|
| **C1** | **Compression** | semantic density, metaphor load, syntactic condensation, rhythm | "Compression Field," compression↔expansion |
| **C2** | **Narrative Structure** | linearity↔fragmentation of event sequencing; causality; time | "Narrative Stability Field" |
| **C3** | **Consciousness Depth** | interiority, POV immersion, subject coherence | "Consciousness Intensity Field" |
| **C4** | **Epistemic Stability** | consistency↔paradox of reality-rules and knowledge | "Ontological Uncertainty Field" |
| **C5** | **Affective Intensity** | emotional volatility and tonal amplitude over time | "Affective Turbulence," Affect |
| **C6** | **Stylistic Residue** *(minor but real)* | voice/signature not reducible to the above | "residual stylistic noise" |

Each axis is a continuous variable in `[0,1]`. A text's position is written `C = (C1, C2, C3, C4, C5)` with C6 as an acknowledged remainder. **Canonical naming rule:** use these names everywhere downstream. The drafts drift between "Affective Intensity" and "Affective Turbulence," etc.; C5 is **Affective Intensity** by decree, and the glossary (§16) is the single source of truth.

**What failed, and why that's the result we wanted.** Several intuitively appealing axes did *not* survive reduction — "semantic density" decomposed into syntax + abstraction + imagery; "voice dominance" turned out inseparable from syntax + rhythm + distance. This is the scientific moment: the system is *not arbitrary* (structure emerged) but it is *not what we assumed* (30 clean dimensions became ~5 entangled ones). Per Charter Principle 3, treat the "five" as a working frame that may collapse further, not as a discovered law of nature.

---

## 8. Layer 3 — The operator basis (Narrative Physics)

Here the model stops describing literature and starts being able to *compute* it. The key shift: stop asking "what are the *dimensions* of literature?" and ask "what are the minimal *transformations* that generate all of it?" A basis element is therefore **not a property; it is an operation** on narrative state.

**The six core operators.** Each `Bᵢ` maps a text-state to a new text-state:

- **B1 — Compression / Expansion.** Folds or unfolds semantic density; metaphor stacking; syntactic compression. *(Generates C1.)*
- **B2 — Temporal Structure.** Reorders narrative causality; linearity↔fragmentation; time dilation. *(Generates C2.)*
- **B3 — Consciousness Interiorization.** Shifts external event ↔ internal perception; POV depth. *(Generates C3.)*
- **B4 — Epistemic (De)Stabilization.** Injects or removes paradox; stabilizes or dissolves reality-rules. *(Generates C4.)*
- **B5 — Affective Amplification.** Scales emotional-field dynamics; intensity gradients; tonal shifts. *(Generates C5.)*
- **B6 — Agential Pressure** *(the hidden sixth).* Governs agency↔constraint; whether characters can act at all; resistance↔flow. This is the operator the pure five-axis model was missing — it is what makes a Kafka-state a *trap* rather than merely an unstable one.

**Three consequences that give the system "physics."**

1. **Text is operator composition, not a point.** A passage is a weighted cascade `x = Σ wᵢ Bᵢ` applied to a state — literature as a composition of transformations. In generation, the LLM becomes a *rendering layer*, not the source of structure.
2. **The operators do not commute.** `B1·B4 ≠ B4·B1` — compressing *before* destabilizing produces a different text than destabilizing *before* compressing. This order-dependence is what yields narrative-physics-like behavior (in plain terms: *sequence matters*, the way stirring-then-heating differs from heating-then-stirring).
3. **Authors are distributions over operators.** Not points, not laws — regions. Woolf ≈ high B3 + high B5 + moderate B1; Borges ≈ high B4 + high B1 + recursive feedback; Kafka ≈ high B4 + high B6 + blocked B2; Hemingway ≈ high B2 + high B6 + low B3. These are *projections we happen to have names for* (Charter Principle 7), and the basis is only *locally* complete — different genres may require a rotated basis, because literary space is a manifold, not a fixed grid.

**Archetypes as eigenstates.** A recognizable archetype is a *stable attractor combination* of operators — a configuration the dynamics settle into. ("Eigenstate/attractor" here just means a self-reinforcing configuration the system tends to fall toward.) A "Kafka state" is the basin where high B4 + high B6 + blocked B2 lock together. This is the formal bridge to L5.

---

## 9. Layer 4 — The interpretation tensor

L1–L3 quietly assumed a text *has* coordinates. It doesn't — it has coordinates *relative to a reader*. L4 makes that explicit and turns reader disagreement into structured data (Charter Principle 2).

**The core object.** Each reader is a stochastic projection `f_r : text → probability distribution over [0,1]⁵` — a reader maps text to a *distribution*, not a point. The interpretation tensor is the resulting three-way array:

```
   T(x)[r, i]  =  P(Cᵢ | x, r)          indexed by  text × reader × axis
```

(A "tensor" here is just a multi-dimensional table — here, one axis-distribution for every reader-and-axis pair.) Each cell stores a distribution's mean, variance, and entropy. From the tensor we derive:

- **Consensus vector** — mean across readers (the "community reading").
- **Disagreement vector** — variance across readers (where readers diverge).
- **Interpretation entropy** `H(x)` — aggregate uncertainty. *Low H → stable meaning; high H → an ambiguous "depth field."*

**Why this resolves the drafts' central anxiety.** "No ground truth" stops being a fatal flaw and becomes the design: there is no true vector, only a distribution plus its *invariants* (the structure that survives across readers). Meaning is redefined as *the invariant structure of the distribution over reader projections*. Archetypes become statistical shapes (a basin of high-C2-variance + low-C4 + skewed-C5), not labels. The reader model is a small parameter set (compression bias, ambiguity tolerance, emotional amplification, structure preference) so that disagreement is *generated structurally* rather than hand-waved.

---

## 10. Layer 5 — The archetype / symbolic overlay

Belief systems — tarot, I-Ching, myth, religion — already solved a problem adjacent to ours: compressing overwhelming complexity into a small set of recurring transformation patterns operating under uncertainty. They are not competitors to the coordinate system; **they are human-readable coordinate systems laid over it.** Their entire license is Charter Principle 6: *summarize, never define.*

The overlay is a two-layer scheme:

- **Layer A — continuous phase space** (the Big Five dynamics from L2/L3).
- **Layer B — discrete archetypal overlay** that names regions and, crucially, *transitions* between them.

What each tradition contributes, translated correctly:

- **Tarot → an event/state classifier.** It supplies a *discrete transition language* the continuous model lacks. Instead of "C4 dropped to 0.18 while C5 spiked to 0.85," you say **"a Tower event occurred"** — a sudden regime shift, a structural rupture, a reality-reinterpretation. Formally: crossing a threshold in C-space fires a named phase-transition.
- **I-Ching → a dynamic update-rule system.** It is essentially a transformation system over binary state-vectors — a near-direct analogue of discretized C-space transitions.
- **Myth → a pretrained multi-agent system.** Gods, heroes, tricksters are stable attractor dynamics of interacting narrative agents (feeds L7 directly).
- **Religion → teleological attractor basins.** It adds *directionality*: narratives that move toward salvation / fall / enlightenment / dissolution states — global basins in C-space.

The payoff is a dual-mode system: continuous simulation underneath, human-readable symbolic compression on top. Used with discipline it is the most communicative layer in the stack; used without discipline it is the most dangerous (symbolic overfitting, §3).

---

# PART IV — THE ENGINE

## 11. Layer 6 — The generative engine

This is where the theory becomes a writing tool (Deliverables D2/D3). The engine is *stateful and evolving*, not a one-shot prompt — that statefulness is exactly what separates a simulator from a generator.

**The pipeline.**

```
  slider input (C1–C5 + optional style seed)
        │  normalize to control bands (low / med / high / extreme)
        ▼
  CONSTRAINT COMPILER   — turn each axis into generation *rules*, not descriptions
        ▼
  STORY STATE MACHINE   — maintain a world-state vector across paragraphs
        ▼
  PROMPT TRANSLATION    — emit a structured constraint spec
        ▼
  RUNTIME COGNITION     — render sentence-by-sentence (the Style Engine, below)
        ▼
  prose  →  state update  →  next step        (feedback loop = simulation)
```

The compiler is the pivot: `C1 high` becomes *"nested clauses allowed, metaphor stacking, implicit meaning encouraged,"* not *"be dense."* The state vector (time position, character intensity, epistemic drift, emotional energy, unresolved threads) is updated after each paragraph, so C2 advances time, C4 introduces controlled "glitch events," C5 drives the tension wave. Emergent genres appear as *phase states* of the dials — e.g. `high C1 + low C4 → metaphysical hallucination prose`; `high C2 + high C5 → procedural emotional thriller`; `low C1 + high C5 → minimalist emotional shock`.

### 11.1 The Runtime Cognition Model (the Style Engine)

The renderer at the bottom of the pipeline is not "apply a style" — it is *simulated cognition rendered in language*. A scene is **resolved from conflicts between five stateful subsystems**, not written linearly:

- **World State (WS)** — ground truth. 3–7 concrete facts per scene, ≥2 physical objects, no emotion or interpretation. *("A man returns to an apartment. A glass sits on a table. Power is partial. A door is closed.")*
- **Perception Layer (PL)** — POV distortion via a per-character filter: *Realist* (high fidelity), *Noir* (moral weight added to objects), *Expressionist* (environment mirrors emotion), *Sebald* (documentary tone, emotion suppressed), *Modernist* (fragmented cognition). PL may distort WS but cannot invent new WS objects except through MF interference.
- **Memory Field (MF)** — the source of uncanny continuity. Stores prior object-states, emotional residues, misremembered facts, symbolic overwrites. Objects may "drift state" across scenes without WS justification; contradiction is allowed if it feels *accumulated*, not random. *(Glass is empty → MF insists it was full earlier → tension.)*
- **Emotional Field (EF)** — emotion as the *physics of attention*, 0–5. It governs what gets zoomed in on: 0 neutral observation → 3 distortion of emphasis → 5 reality read entirely through feeling.
- **Language Register (LR)** — chosen per sentence: plain realist / noir-compressed / elevated literary / clinical / archaic (rare) / fragmented modernist. **Rotation rule: no register persists more than two consecutive sentences.**

Bolted onto these:

- **Character system** — each character carries a *cognitive bias profile* (literal / interpretive / paranoid / dissociative / procedural), an *emotional temperature* range that shifts scene-by-scene, and 2–3 *object anchors* they subconsciously track.
- **Dialogue deformation** — speech is filtered cognition, not transcription. The same line bends by filter: *"I don't remember leaving the light on"* → Noir *"I didn't leave it on."* → Modernist *"I—did I—no, I wouldn't—"* → Expressionist *"That light shouldn't be alive in there."* → Sebald *"He said he did not recall leaving the light on."*
- **Scene tension curve** — every scene follows five phases: **Establishment** (EF 0–2, stable) → **Drift** (2–3, minor inconsistencies) → **Pressure** (3–4, objects gain memory/emotional weight) → **Breakdown** (4–5, reality goes interpretively unstable) → **Residue** (ends on an unresolved object state).
- **Object memory system** — *objects are the only carriers of continuity, not plot.* Each key object has a state timeline (physical changes, perception variations, memory contradictions). A glass across three scenes: full → half-evaporated → "was never filled today" (MF conflict). Story rides the objects.

This subsystem is the operational heart of D2: dialing C1–C5 sets the parameters; WS/PL/MF/EF/LR resolve them into sentences. It is also the natural place to encode a *specific* voice — for example the project's own house style (a Realism + Sebald + Expressionism primary engine, with Noir/Modernist/Symbolist secondary color: realist sentence structure, restrained documentary drift, controlled perceptual misalignment rather than the supernatural).

---

## 12. Layer 7 — The multi-agent simulation

The final zoom-out: stop asking "how do I generate prose?" and ask **"what happens when incompatible theories of writing compete in the same world?"** Woolf, Borges, Kafka, Hemingway stop being presets and become *agents with mutually incompatible narrative physics* operating on one shared reality.

```
                ┌─────────────────────┐
                │  GLOBAL WORLD STATE │   time, epistemic stability,
                └──────────┬──────────┘   emotional pressure, entropy, events
             ┌─────────────┼─────────────┐
        ┌────────┐    ┌────────┐    ┌────────┐
        │ Woolf  │    │ Borges │    │ Kafka  │   each: perceive(world) → act →
        │consci. │    │epistem.│    │constr. │   (text fragment + world delta)
        └────────┘    └────────┘    └────────┘
             └─────────────┼─────────────┘
                ┌─────────────────────┐
                │  CONFLICT RESOLVER  │   merges / reconciles competing deltas
                └──────────┬──────────┘
                ┌─────────────────────┐
                │   EMERGENT TEXT     │   story = equilibrium or sustained conflict
                └─────────────────────┘
```

Each agent `perceive`s the shared world through its bias and `act`s by proposing a text fragment plus a world-state modification; the conflict resolver reconciles the competing proposals; story emerges as either an equilibrium or a sustained antagonism between force-laws.

**The named risk this layer must engineer against** (Charter Principles 4 & 7): LLMs *smooth contradictions*. Left alone they'll collapse "Woolf + Borges + Kafka tension" into "mildly surreal interior prose with paradox flavor" — losing the actual multi-force interference that is the entire point. And a single agent can dominate (Kafka suppresses all action; Borges dissolves coherence; Woolf stalls time), deadlocking the system. The conflict resolver's real job is *preserving* antagonism, not resolving it. This is the hardest engineering problem in the stack and should be treated as research, not a feature checkbox.

---

# PART V — THE DESCRIPTIVE DIMENSIONS

## 13. The Work-Description Space (orthogonal to the stack)

The drafts end with an enormous genre catalogue and a genuinely important realization buried inside it — one that powers Deliverable D3 (combinatorial ideation).

**The insight:** most of the "-punk" labels (cyberpunk, biopunk, solarpunk, mythpunk, and dozens more) *are not genres at all.* A "punk" specifies a technology source, material culture, dominant motifs, economic structure, political assumptions, and characteristic tensions. That is a **Setting / Aesthetic Paradigm** — a *worldbuilding framework*, not a story category.

Which means a work is described by *several independent dimensions at once*, not one competing "genre" slot:

- **Genre** (mystery, horror, romance, tragedy…)
- **Tone** (bleak, comic, elegiac, absurd…)
- **Theme** (identity, power, entropy, grief…)
- **Narrative structure** (linear, fragmented, recursive, epistolary…)
- **Philosophy** (existential, deterministic, nihilist, humanist…)
- **Emotional signature** (dread, awe, alienation, tenderness…)
- **Stylistic signature** (documentary, poetic, surreal, minimalist…)
- **Setting-aesthetic paradigm** (cyberpunk, biopunk, dieselpunk, solarpunk…)

This is why *"biopunk noir cosmic-horror transhuman detective fiction"* is perfectly coherent despite sounding ridiculous — the labels name **different axes**, not rival genres. Cross-producting these axes is a combinatorial idea-generator: it manufactures premises and genre-fusions that don't yet exist. Note the clean division of labor — the Work-Description Space is *label space* (how we describe a finished work), entirely distinct from the *generative space* (L3/L6) that produces it and the *interpretation space* (L1/L4) that reads it. It sits beside the stack, not inside it.

---

# PART VI — EXECUTION

## 14. Roadmap (phase-gated, with exit criteria)

Each phase gates the next; do not advance until the exit criteria are met. This ordering deliberately front-loads the *honest* work (does the instrument even work?) before the *fun* work (generation).

**Phase 0 — Charter & spec freeze.** *This document.*
Exit: canonical axis names, the stack, and the Epistemic Charter are agreed and frozen. → **complete on acceptance of this file.**

**Phase 1 — Build the instrument.** Finalize the L1 rater manual and assemble the 30-segment pilot corpus (canonical anchors + deliberate redundant pairs for reliability testing, spanning maximal stylistic/structural/philosophical/affective contrast).
Exit: manual + corpus exist; two independent raters (one human, one LLM) can each complete a full segment end-to-end without ambiguity in the *procedure*.

**Phase 2 — First measurement run + reliability analysis.** Rate the corpus. Compute inter-rater agreement, the axis correlation matrix, and run PCA.
Exit: you can state, with numbers, (a) which axes are reliable, (b) which are redundant and should merge, (c) which are ambiguous and need redesign, and (d) the emergent latent-factor structure. **This is the moment the framework either crystallizes or reveals a more interesting shape** — either outcome passes the phase; refusing to look does not.

**Phase 3 — Coordinate System v1.** Lock the surviving Big Five (+ residual). Build mapping/visualization: place texts and authors as coordinates; render trajectories through C-space; surface emergent clusters.
Exit: an arbitrary new segment can be projected into the space and its nearest neighbors make intuitive sense to a human reader.

**Phase 4 — Generative Engine MVP.** Implement the L6 pipeline as a single runnable system: slider → band-normalizer → constraint compiler → story state machine → prompt spec → LLM render → state update, with dial-a-preset configs and the Runtime Cognition subsystems (WS/PL/MF/EF/LR).
Exit: moving a single slider produces a *legibly different* prose behavior across repeated runs; state visibly evolves across paragraphs (it is a simulator, not a prompt).

**Phase 5 — Interpretation Tensor + Archetype Overlay.** Add the L4 reader-model tensor (consensus / disagreement / entropy) and the L5 phase-transition classifier (threshold-triggered named events).
Exit: the system reports interpretive variance for a passage *and* names at least one regime transition, with both grounded in measured state rather than asserted.

**Phase 6 — Multi-Agent Simulation.** Implement L7: shared world state, agent perceive/act loop, and a conflict resolver whose explicit objective is *preserving* inter-agent antagonism.
Exit: a run demonstrably preserves competing narrative physics (measurable multi-force interference) rather than collapsing to a single dominant voice.

**Cross-cutting, every phase:** honor the Charter. Keep the descriptive and generative models firewalled (P4). Keep a residual axis (P5). Prefer defaults and presets so the tool never paralyzes the writer (P9).

---

## 15. Repository / artifact structure

A buildable shape you can hand to Claude Code. It matches the phase-gated, milestone-driven, git-diffable-markdown conventions used across the rest of your projects (a `PROGRESS.md`/`ROADMAP.md` workflow with explicit exit criteria, an `ARCHITECTURE.md`, a `DECISIONS.md`).

```
lsap/
├── README.md                     # elevator pitch + link to this blueprint
├── LSAP_Foundational_Blueprint.md# this file — the canonical spec (L0–L7 + charter)
├── ROADMAP.md                    # Part VI, as living phase gates + exit criteria
├── DECISIONS.md                  # every canonical choice + why (axis names, firewall…)
├── ARCHITECTURE.md               # the stack as an engineering diagram
├── docs/
│   ├── charter.md                # §3 extracted — the load-bearing constraints
│   ├── craft-primer.md           # L0 grammar/craft curriculum (pedagogy sub-module)
│   ├── glossary.md               # §16 — single source of truth for terms
│   └── work-description-space.md # Part V — the descriptive axes + combinator
├── instrument/                   # Layer 1
│   ├── rater-manual.md           # golden rules, 4-pass workflow, 7-pt scale
│   ├── axes.md                   # the 30 axes, anchored definitions
│   ├── corpus/                   # 30-segment pilot corpus (+ redundant pairs)
│   └── scoring/                  # rating outputs, reliability + PCA notebooks
├── coordinates/                  # Layers 2–3
│   ├── big-five.md               # C1–C6 canonical spec
│   ├── operators.md              # B1–B6 operator algebra (non-commutative)
│   └── projection/               # map/visualize C-space; trajectories; clusters
├── engine/                       # Layers 6–7
│   ├── compiler/                 # slider → bands → constraints
│   ├── state-machine/            # stateful narrative loop
│   ├── runtime-cognition/        # WS · PL · MF · EF · LR + character/dialogue/objects
│   ├── presets/                  # dial-a-writer configs
│   └── simulation/               # world state · agents · conflict resolver
└── interpretation/               # Layers 4–5
    ├── tensor/                   # reader models; consensus / disagreement / entropy
    └── archetypes/               # attractor basins + phase-transition classifier
```

**Suggested `CLAUDE.md` posture** (consistent with how you already run Claude Code): autonomous execution without clarifying questions; phase-gated milestones with explicit exit criteria as above; a standing "continue" instruction sufficient to resume; markdown as the documentation format; and — specific to *this* project — a hard rule that the analysis model (`instrument/`, `coordinates/projection/`) and the generative model (`engine/`) are never wired directly into each other (Charter Principle 4).

---

## 16. Glossary (canonical terms)

The single source of truth. Where the drafts disagree, this wins.

- **LSAP** — Literary Space Annotation Protocol. The umbrella program (this whole system).
- **UTL** — Unified Theory of Literature. The theory layer (L0 substrate + the claim that literary structure is inherited from other disciplines).
- **LSAP-1** — version 1 of the annotation instrument + coordinate system (Layers 1–2, extended upward through the stack).
- **Segment** — a coherent scene-unit of prose, ~1,000–3,000 words; the atomic unit of rating.
- **The 30 axes** — observable features scored 1–7 across six fields (Language / Narrative / Consciousness / Philosophy / Affective / Stylistic). *Layer 1.*
- **Big Five (C1–C5) + C6 residual** — the latent coordinate space the 30 axes collapse into via PCA. Canonical names: **C1 Compression · C2 Narrative Structure · C3 Consciousness Depth · C4 Epistemic Stability · C5 Affective Intensity · C6 Stylistic Residue.** *Layer 2.*
- **Operators (B1–B6)** — the irreducible generative transformations: Compression/Expansion · Temporal Structure · Consciousness Interiorization · Epistemic (De)Stabilization · Affective Amplification · Agential Pressure. Non-commutative. *Layer 3.*
- **Non-commutative** — order-dependent; applying B then A differs from A then B. The source of "narrative physics."
- **PCA (Principal Component Analysis)** — statistical method that finds the few underlying dimensions explaining most variation in a larger measurement set. How L1 → L2.
- **Interpretation tensor `T(x)[r,i]`** — a text × reader × axis table of probability distributions; encodes interpretive plurality. Yields consensus, disagreement, and entropy. *Layer 4.*
- **Consensus / Disagreement / Entropy** — mean across readers / variance across readers / aggregate uncertainty of a reading.
- **Archetype** — a stable attractor basin (eigenstate) of operator dynamics; a *region*, never a label. *Layers 3 & 5.*
- **Attractor basin / eigenstate** — a self-reinforcing configuration the dynamics tend to settle into.
- **Phase transition (e.g., "Tower event")** — a named, threshold-triggered regime shift in C-space. *Layer 5.*
- **Symbolic overlay** — tarot / I-Ching / myth / religion as human-readable coordinate landmarks over the continuous space. Summarizes; never defines.
- **Runtime Cognition Model** — the L6 renderer: WS (World State) · PL (Perception Layer) · MF (Memory Field) · EF (Emotional Field) · LR (Language Register), plus character, dialogue-deformation, tension-curve, and object-memory subsystems.
- **Work-Description Space** — the orthogonal set of descriptive axes (genre, tone, theme, structure, philosophy, emotional signature, stylistic signature, setting-aesthetic paradigm). *Part V; label space, not a stack layer.*
- **Setting / Aesthetic Paradigm** — a worldbuilding framework (the "-punk" family); a technology/material/economic/political/motif bundle, distinct from genre.
- **The three spaces** — **generative** (produces text: L3/L6), **interpretation** (reads it: L1/L4), **label** (describes it: L2/L5/Part V). Never conflate them.

---

*End of foundation. Everything else is downstream.*
