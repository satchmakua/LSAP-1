# PROGRESS — LSAP-1

A build log of what shipped and the notable decisions behind it. **Keep it honest** —
this is the working memory between build sessions. The forward-looking plan and
acceptance tests live in [ROADMAP.md](ROADMAP.md); this is the "what got done and why"
companion.

**Current phase:** **Phase 4 (v1 hardening) is underway — M5 is done; M6 is next.**
The v1 slice (M0–M4) is complete: rate a segment on 30 anchored axes, watch it land in
a fitted C-space beside its kin, dial the operators to generate measurably different
prose — firewall intact throughout. M5 re-anchored the two absolute-ambiguous axes:
L3 is fixed (0.40 → 0.83); L1 resisted two revisions and is written up as a
split/retirement candidate (see the M5 entry — **decide with the human before M6**).

### State of the tree

| Area | Where | Status |
|---|---|---|
| API surface | `backend/src/lsap/api/app.py` | `/health`, `/api/axes`, `POST /api/rate`, `/api/segments[/{id}]`, `/api/cspace`, `/api/segments/{id}/projection`, **`GET /api/presets`, `POST /api/generate`** |
| Instrument | `backend/src/lsap/instrument/` | `schema.py` + 30-axis `axes.yaml` (**version 3** — L1/L3 re-anchored in M5); **`rater.py` implemented** (Claude structured output, stamps `axes_version`) |
| Persistence | `backend/src/lsap/storage.py` | JSONL ratings + markdown corpus (git-diffable); `latest_ratings` = newest-wins per (rater, segment, axes_version) |
| Corpus & data | `corpus/*.md`, `ratings/*.jsonl`, `reliability/` | 30-segment pilot (`source: pilot`) + 180 ratings across 3 anchor cohorts + reliability report (v1 vs v3 before/after) |
| Coordinates | `backend/src/lsap/coordinates/` | **`reliability.py` + `projection.py` implemented** (N-rater per-pair agreement / correlation / PCA / twins; fitted + persisted projection, neighbours; cohort-aware) |
| Fitted model | `coordinates/model.json` | 5 locked factors over 30 segments (axes_version 3), 79.2% explained, C6 residual 20.8% |
| Engine | `backend/src/lsap/engine/` | **fully implemented** — `compiler.py` (rule tables, derived B6), `runtime.py` (state machine + WS/PL/MF/EF/LR loop), `presets.yaml`, `operators.yaml` |
| Firewall | `backend/tests/test_firewall.py` | enforced & green (hardened: every import form + `storage`) |
| Frontend | `frontend/src/` | Tabbed: Rater Studio (rate → 30 axes) + C-Space Map (scatter, neighbours) · **Engine Console** (5 sliders, presets, per-paragraph state panel, re-rate) |

---

## M5 — Rating-selection defect fix + re-anchor L1 & L3 · built & verified 2026-07-19 · ✓ (stop rule fired for L1)

The first hardening milestone, and the first honest negative result: one axis fixed
decisively, one axis shown to be beyond anchor repair — which is itself the finding.

**Shipped**
- **The defect fix (prerequisite for all of Phase 4).** Both analysis loaders took the
  *first* rating per (rater, segment) while `save_rating` appends — every re-rate was
  written to disk and silently ignored. Selection is now **newest-wins per (rater,
  segment, axes_version)** via `storage.latest_ratings`; `Rating.axes_version` (defaults
  to 1 so the 60 stored ratings parse unchanged) is stamped from a new `version:` key in
  `axes.yaml`, so ratings scored under different anchors can never be silently pooled.
  Loader/consensus tests append a second rating and assert the newer one is used.
- **N-rater `build_report`** (started by a concurrent session; kept and finished):
  per-pair agreement with pairwise-complete/ragged coverage — M7's prerequisite arrived
  early. Plus a **before/after section** comparing the current cohort to the *oldest*
  (pre-re-anchor baseline), columns labelled by `axes_version`, with a >0.10-regression
  flag. `rate_corpus.py` resumability is version-aware: bumping `version:` queues a full
  re-rate. `fit_from_storage` fits one cohort only and records it in `model.json`; the
  projection endpoint projects with the model's own cohort.
- **Anchors v2** (both axes, drafted by a 4-lens draft → 3-judge → synthesize workflow):
  countable referents with full count-to-score maps — L1 as *marked words per 100* with
  example words per band; L3 as *propositions per sentence* averaged over five
  consecutive sentences, worked counts shown. **Anchors v3** (L1 only, final allowed
  revision): after diagnosing that Haiku rates in one pass with no thinking room — a
  counting procedure can't bite — each band gained a self-annotated **exemplar sentence**
  (recognition channel pinned to the arithmetic channel), plus a negative exemplar:
  atmospheric prose of common words scores 1–2.

**Findings (30 segments × 2 raters × 2 re-rates ≈ 180 paid calls; all 60/60 twice, 0 failed)**
- **L3 Semantic Density: 0.40 → 0.67 → 0.83 within-1 ✓.** The proposition-count anchor
  fixed it; now among the stronger axes (Spearman ~0.74 held throughout).
- **L1 Lexical Complexity: 0.40 → 0.37 → 0.30 ✗ — the stop rule fired.** The decisive
  signature: both raters recalibrated downward nearly in lockstep (Opus 3.30 → 2.33 →
  2.13; Haiku 4.93 → 4.17 → 3.97) while the offset froze at **+1.8** and Spearman held
  ~0.75. The anchors moved both raters; nothing moved them *together*. "Rare word" is
  rater-relative — the two models carry different effective vocabularies, so "rare for
  whom?" has no anchor-fixable answer. Per Charter P2 this disagreement is data.
  **Disposition (for the human, before M6):** split (technical/specialist rarity vs
  literary-register elevation) or retire toward the cluster it already rides with
  (L1~L2 r=0.87, L1~L3 r=0.86 in the pilot).
- **N3 Causal Clarity destabilized with no anchor change: 0.73 → 0.60 → 0.40**, offset
  growing 0.50 → 1.07 → 1.27, Spearman 0.38–0.49 (always the second-weakest ranker).
  Its v1 0.73 was riding on a small offset that drifted between runs — within-1 at n=30
  carries real run-to-run variance, and axis stability under re-measurement is now a
  known question M6's larger n should answer. Watch list, not retuned (the M5 stop rule
  scopes anchor surgery to L1/L3).
- All other axes within −0.10 of their v1 baseline (P4 exactly −0.10; several improved:
  S4 +0.23, S3 +0.13, A2 +0.13). **27/30 reliable** (was 26); ambiguous: L1, N3.
- **Projection refit on the v3 cohort:** 5 factors, 79.2% explained, C6 residual 20.8%
  (vs 79.4/20.6 pre-refit — the frame is stable). Twin nearest-neighbour **6/8** (was
  7/8; `elegy-station` now lands one neighbour off — `letter-confession` — with its twin
  second).

**Verified**
- Backend `pytest` → **76 passed** (adds selection/cohort tests in storage, reliability,
  projection; rater stamping; old-JSONL parse compat; registry-version guard); `ruff`
  clean. Frontend `vitest` → **6 passed**; `build` + `oxlint` clean. Firewall green.
- Live API smoke: `/health` ok (30 axes), `/api/cspace` serves the refit model
  (residual 0.2078, n=30), `min-kitchen`'s projection returns its twin
  `min-laundromat` first at the refit distance.

**Decisions**
- **Newest = last line in the append-only file** (file order is chronological); no
  timestamp parsing. Cohorts are never pooled — a re-anchored axis changes what a score
  *means*, so cross-version averaging would be silent nonsense.
- **"Before" in the report = the oldest cohort**, not the previous revision — the
  standing question is "did re-anchoring help vs the original instrument".
- **The stop rule is a feature, not a failure.** Two revisions were spent; continuing
  to tune until two models agree would invert P2 (manufacture agreement instead of
  measuring it). The honest exit is the write-up above.

---

## M4 — Generative Engine MVP · built & verified 2026-07-03 · ✓

The milestone the whole architecture exists to protect. The engine writes from operators
and rules only — it has never seen the coordinate space fitted in M3 — and moving one
slider moves the instrument's own measurements in the predicted direction.

**Shipped**
- **`engine/compiler.py`** — the pivot. Each dial band maps to a table of *instructions*
  ("Nested clauses are allowed.", "Stack metaphors.", "Report only what a camera would
  record.") rather than adjectives. Plus **B6 agential pressure derived, not dialled**
  (`(c4 + (1 - c2)) / 2` — instability against blocked time is what makes a trap), a
  perception filter (realist / noir / sebald / expressionist / modernist), and a language-
  register palette guaranteed ≥2 so rotation always has somewhere to go.
- **`engine/runtime.py`** — the deterministic state machine + rendering loop. Phase walks
  establishment → drift → pressure → breakdown → residue; emotional energy follows the
  phase curve scaled by c5; the register rotates every paragraph; the memory field makes
  objects recur (stable dials) or contradict the world (c4 ≥ med). Claude renders one
  paragraph per step — the loop, not a single prompt, is what makes it a simulator.
- **`engine/presets.yaml`** (house / minimal / baroque / hallucinatory / thriller / trap),
  `GET /api/presets`, `POST /api/generate`, and the **Engine Console** (5 sliders with live
  bands, preset picker, per-paragraph state panel, world-state disclosure, re-rate button).
- **`scripts/engine_ab.py`** — A/B one dial and re-rate both runs. The sanctioned one-way
  crossing lives in a *script*, never in `engine/`.

**Verified**
- `uv run pytest` → **67 passed** (13 engine + 4 engine-endpoint added); `ruff` clean.
  Frontend `vitest` → **6 passed**; `build` + `oxlint` clean. **The firewall test stayed
  green** — `lsap.engine` imports only `lsap.config` and the SDK.
- **Live A/B on c1** (`--dial c1 --paragraphs 4`), same situation both runs:
  mean sentence length **6.3 → 140.5 words**. A: *"The man stood inside the doorway. He had
  not been here for months."* B: *"The brass key turned in a lock that gave with the
  reluctance of a throat clearing itself of some old, unsaid thing…"*
- **Re-rating moved 4/4 expected axes up**: L2 Syntactic Depth **1→7**, S4 Figurative
  Density 2→6, L3 Semantic Density 2→5, L1 Lexical Complexity 1→4.
- State advanced per paragraph: phases `[establishment, drift, pressure, residue]`,
  registers alternating every step, energy `[0.5, 1.4, 2.7, 3.1]`.

**Notes**
- Generation is a loop of small calls (one seeding + one per paragraph), so no single call
  needs streaming; `max_tokens` stays well inside the non-streaming envelope.
- `Paragraph.language_register` is deliberately not named `register` — that shadows
  `BaseModel.register` and pydantic warns.

---

## M3 — Coordinate system v1 · built & verified 2026-07-03 · ✓

Locked the surviving factors, fitted and persisted the projection, and put an arbitrary
new segment on the map next to neighbours that actually read as its kin.

**Shipped**
- **`coordinates/projection.py`**: fit (consensus → standardize → PCA) → persist →
  project → nearest neighbours. `scripts/fit_projection.py` fits over the pilot corpus,
  writes `coordinates/model.json`, and self-checks the twin-pair criterion.
- **API**: `GET /api/cspace` (factors + corpus points) and
  `GET /api/segments/{id}/projection` (vector + neighbours); both 409 until a model is fitted.
- **Frontend `CSpaceMap`**: SVG scatter with selectable factor axes, per-axis variance
  share, the acknowledged residual, the rated segment highlighted, and a neighbour list.

**The fitted coordinate system** (30 segments, 5 factors, **79.4% explained, C6 residual 20.6%**)

| | var | derived label (from its own top loadings) |
|---|---|---|
| C1 | 44.8% | Figurative Density · Interior/Exterior Ratio · Cognitive Transparency |
| C2 | 11.5% | Meaning Structure · Moral-Structure Clarity · Intensity Curve |
| C3 | 10.5% | Emotional Volatility · Semantic Density · Lexical Complexity |
| C4 | 7.0% | Plot Centrality · Rhythm Regularity · Lexical Complexity |
| C5 | 5.5% | Rhythm Regularity · Event Density · Repetition Pattern |

**Decisions (both forced by the data — DESIGN §4.2 was rewritten to match)**
- **Derived factor labels, not the hypothesised names.** The blueprint's proposed
  C1..C5 names don't map 1:1 onto the fit, so each component is labelled from its own top
  loadings. Naming a factor after what it actually loads on avoids the symbolic-overfitting
  trap (Charter P6).
- **Neighbour distance in raw PCA-score space.** Raw scores are variance-weighted, so the
  dominant factors drive similarity; the [0,1] display coords would give a
  near-zero-variance direction equal weight to PC1. Degenerate components are dropped at
  fit time (found via a test where a ~0%-variance direction made `project()` disagree with
  its own fitted point).

**Verified**
- `uv run pytest` → **50 passed** (adds 7 projection + 4 C-space endpoint tests);
  `ruff` clean. Frontend `vitest` → **4 passed**; `build` + `oxlint` clean.
- **Twin criterion: 7/8** twin-pair members have their twin as nearest neighbour. The one
  miss is defensible — `paradox-library` landed nearest `second-person-city` (both cool,
  meta, epistemically unstable), with `paradox-map` next.
- **End-to-end in the running app**: a brand-new minimalist passage rated through the UI
  projected as a highlighted dot whose neighbours were `min-kitchen` (1.66),
  `min-laundromat` (4.11), `catalogue-estate` (4.39), `scifi-clinical` (5.76) — the two
  deliberately-minimalist twins first, then the other flat/documentary segments. 30 corpus
  dots + the new point rendered, no console errors. (Screenshot capture times out in this
  environment; verified via DOM/JS inspection.)

---

## M2 — Pilot corpus + reliability · built & verified 2026-07-03 · ✓

Built the honest measurement pass: a contrast-spanning corpus, both raters over all of
it, and a reliability analysis — and the result is the crystallization moment the
blueprint predicted (§7).

**Shipped**
- **Pilot corpus** (`corpus/*.md`, `source: pilot`): 30 original ~1,200-word segments,
  each written by Claude to a purely *structural* brief (no author imitation — Charter
  P7) spanning the axis extremes — compressed↔baroque, linear↔fragmented,
  exterior↔stream-of-consciousness, stable↔paradoxical, flat↔volatile, documentary↔
  poetic↔surreal↔experimental — with **4 redundant twin-pairs** (same profile, different
  scene) for consistency testing. Specs in `scripts/corpus_specs.json`.
- **Runners**: `scripts/generate_corpus.py` (concurrent Opus generation, idempotent) and
  `scripts/rate_corpus.py` (both raters, concurrent, resumable — skips already-rated).
- **Reliability** (`coordinates/reliability.py`): per-axis inter-rater agreement (ordinal:
  within-1 / Spearman / weighted-κ / |Δ|; forced-choice: exact-match / κ) + mean
  confidence; the scalar-axis correlation matrix (redundancy); PCA (latent factors); and
  twin-pair consistency. Writes `reliability/report.md` + `metrics.json`. Pure metrics are
  unit-tested offline.

**Findings (60 live ratings, Opus 4.8 vs Haiku 4.5, n=30)**
- **26 of 30 axes reliable**; **2 absolute-ambiguous**: L1 Lexical Complexity and L3
  Semantic Density (within-1 = 0.40, |Δ| ≈ 1.6) — the models *rank* segments together
  (Spearman ≈ 0.75) but calibrate the 1–7 scale differently. Redesign/anchor candidates.
- **The Consciousness field collapses**: C1 Narrative Distance ~ C3 Cognitive
  Transparency ~ C5 Interior/Exterior are one factor (r = 0.93–0.96); the Language
  compression axes (L1/L2/L3/S4) cluster too. Exactly the blueprint's "30 clean
  dimensions → ~5 entangled ones."
- **PCA supports the Big Five**: PC1 explains **44.8%** of variance, ~**6 components cover
  80%** (8 for 90%). PC1 = interiority/compression, PC2 = meaning/philosophy, PC3 =
  affect — the hypothesized C-space has real structure, not noise.
- **Twin consistency**: same-profile twins are **3× closer** than random pairs
  (mean |Δ| 0.51 vs 1.49) — the instrument gives consistent scores to equivalent inputs.
- Lowest-confidence axes: P3 Moral-Structure (3.5), A5 Resolution, P5 Agency, P4 Meaning
  — the Philosophy field is the hardest to score confidently.

**Decisions**
- **Corpus is Claude-authored original prose, not scraped canon** — copyright-clean, and
  it lets us *design* the contrast + twin structure the reliability test needs.
- **Two models as the two "raters"** (Opus vs Haiku) is a reliability proxy; true
  reliability wants a human rater too (future). Framed honestly.
- **PCA over the 27 scalar axes only**; forced-choice (A3/A5/S5) analysed by agreement,
  not one-hot into PCA — with n=30 one-hot (DESIGN §4.2) would be degenerate. M3 locks
  the projection.

**Verified**
- `uv run pytest` → **39 passed** (adds 7 reliability-math tests: agreement, correlation,
  PCA concentration, twins). `ruff` clean.
- `uv run python -m lsap.coordinates.reliability` over the 60 real ratings → the report
  above; artifacts at `reliability/report.md` + `metrics.json`.
- Generation: 30/30 segments, 1,198–1,374 words, 0 failures. Rating: 60/60, 0 flagged.

---

## M1 — The rater · built & verified 2026-07-03 · ✓

Implemented the L1 instrument end-to-end: a prose segment → a validated 30-axis `Rating`
via Claude structured output, persisted and read back — and verified with a real call.

**Shipped**
- **Rater** (`instrument/rater.py`): forces a Claude structured output shaped as a
  `scores` list of `{axis_id, value, confidence}`, where `axis_id` is a `Literal` enum of
  the 30 ids and `value` is a plain integer (1–7 for scalar axes; the 1-based option
  number for forced-choice — the manual numbers the choices). `to_rating` checks all 30
  are present and clamps to range. The manual (golden rules + every axis's anchors /
  choices / watch-fors) is the cached system prompt; adaptive thinking is gated to
  Opus-class models (Haiku 4.5 supports neither adaptive thinking nor effort).
- **Persistence** (`storage.py`): append-only `ratings/<id>.jsonl` (raters/runs accrue)
  + write-once `corpus/<id>.md` with YAML frontmatter. Repo-root default, `LSAP_DATA_DIR`
  override for tests.
- **API**: `POST /api/rate` (derives a stable segment id, stamps `created_at`, rejects a
  paid rating that would be mis-attributed — see the fix below), `GET /api/segments`,
  `GET /api/segments/{id}`.
- **Frontend**: the Rater Studio rate form (textarea + title + rater picker + word-count
  hint) and a `ScoresView` that renders the 30 scores grouped by field with a value bar,
  forced-choice label, confidence dots, and a flagged banner.

**Decisions & the current API, verified against a real call**
- **Output schema is a flat `scores` list — learned the hard way.** The first shape (a
  30-property object with per-axis `{value, confidence}`) returned `400 "compiled grammar
  is too large"` from strict structured outputs — and still did after dropping the
  int-enums to plain ints. An object with 30 required properties blows up the
  constrained-decoding grammar. A single list of one small element type (`axis_id` a
  30-member enum + two plain ints) stays well under the cap; `to_rating` restores the
  completeness guarantee. Guarded by a schema-shape unit test.
- **Key-wiring fix.** `_default_client` now passes the resolved key to
  `anthropic.Anthropic(api_key=…)`, and `config` reads `backend/.env` by absolute path. A
  key placed in `.env` loads into settings, *not* the process env the SDK's zero-arg
  constructor reads — so the documented `.env` flow was previously silently broken.
- `client.messages.parse(output_format=<model>, system=…, thinking=…)` on **anthropic
  0.116.0**. `claude-opus-4-8` canonical rater (adaptive thinking); `claude-haiku-4-5`
  second rater (no thinking). No `temperature`/`top_p` (400 on Opus 4.8).

**Reviewed** — an adversarial review confirmed the forced-choice indexing,
frontmatter round-trip, ≥30-score guarantee, and error handling are correct, and found
one real defect:
- **Fixed — id↔text mismatch.** `save_segment` is write-once while `save_rating` appends,
  so reusing an id for *different* text (a title-slug collision like `"Chapter One"` vs
  `"chapter one!!!"`, or an edit-then-re-rate) would orphan a rating from its prose. The
  rate endpoint now returns **409** when an id already stores different text.
- **Hardened the firewall test** — its AST scanner missed `from lsap import instrument`
  forms and didn't guard `lsap.storage` (which is analysis-side). Now catches every
  import form; added scanner unit tests.

**Verified**
- `uv run pytest` → **32 passed** (rater schema-shape / conversion / clamp / completeness
  / thinking-gating / key-wiring, storage round-trips, endpoint incl. the 409 guard and
  rerun-append, firewall scanner). `ruff` clean. Frontend `vitest` → **2 passed**;
  `build` + `oxlint` clean.
- **Live rating ✓ (real Opus 4.8 call).** An original 1,135-word interior scene scored to
  a coherent, defensible 30-axis reading — A3 → *grief*, A5 → *unresolved*, S5 → *poetic*;
  N5 experience-over-plot 6, N1 event-density 2, C4 polyphony 1, C5 interior 6, P2
  epistemic-uncertainty 5, S2 length-variance 5 — persisted to
  `ratings/return-to-the-flat.jsonl` (a re-run appended a 2nd rating) and
  `corpus/return-to-the-flat.md`.

---

## M0 — Skeleton & it runs · built 2026-07-02 · ✓ verified

Stood up the hybrid monorepo from the [DESIGN.md](DESIGN.md) spec and got it running
end-to-end.

**Shipped**
- **Backend** (`backend/`, Python 3.11 + FastAPI + Pydantic v2, managed by uv):
  the `instrument` / `coordinates` / `engine` / `api` package tree (mirroring DESIGN §5),
  the real 30-axis registry as data (`axes.yaml`) + the `Rating`/`AxisDef`/`AxisScore`
  schema, and `/health` + `/api/axes` endpoints. Analysis stubs (`rater`, `projection`)
  and the engine `compiler` carry real signatures + `NotImplementedError` pointing at
  their milestones.
- **Firewall** — `tests/test_firewall.py` parses the AST of every `engine/` module and
  fails if it imports the analysis side (Charter P4). Green from day one.
- **Frontend** (`frontend/`, React 19 + Vite 8 + TS 6): the Rater Studio seed — fetches
  `/api/axes` and renders all 30 axes grouped into the six fields, tagging A3/A5/S5 as
  forced-choice. Vite proxies `/api` + `/health` to the backend.
- **Root orchestration** — `package.json` scripts (`dev`/`test`/`lint`/`build`/`setup`)
  drive both halves via `concurrently`. Doc loop (README/DESIGN/ROADMAP/PROGRESS/CLAUDE),
  ADRs (incl. 0002 on the firewall), CI for both stacks, and hygiene files in place.

**Decisions**
- **Hybrid split** (`backend/` + `frontend/`) so each half keeps its own tooling
  (uv venv vs node_modules); a root `package.json` ties them together.
- **Python 3.11, not 3.12.** uv's managed-3.12 download hit a Windows "minor-version
  link" error; the system interpreter is 3.11.9 and nothing in the code needs 3.12, so
  the floor is `>=3.11`. DESIGN/README reconciled.
- **A5 Resolution Type is forced-choice** (three total: A3, A5, S5) — its categories
  (cathartic/unresolved/deflationary/collapse) are nominal, not an ordinal scale.

**Verified**
- `cd backend && uv run pytest` → **7 passed** (health, axes endpoint, schema/registry,
  firewall). `uv run ruff check .` → all checks passed.
- Live boot: `uvicorn` on :8000 → `GET /health` = `{"status":"ok","axes_loaded":30}`;
  `GET /api/axes` = 30 axes, forced-choice `[A3, A5, S5]`.
- `cd frontend && npm test` → **2 passed** (renders header; lists axes + forced-choice
  tag from a mocked fetch). `npm run build` → clean production build. `npm run lint`
  (oxlint) → clean.

**Gotchas for the next session**
- `npm run dev` needs **uv on your PATH** (the `dev:api` script calls `uv run`). Install
  uv via its standalone installer (which adds itself to PATH) rather than only `pip
  install uv`.
- FastAPI's `TestClient` prints a `StarletteDeprecationWarning` about httpx — cosmetic.
