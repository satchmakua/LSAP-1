# PROGRESS — LSAP-1

A build log of what shipped and the notable decisions behind it. **Keep it honest** —
this is the working memory between build sessions. The forward-looking plan and
acceptance tests live in [ROADMAP.md](ROADMAP.md); this is the "what got done and why"
companion.

**Current phase:** M2 (pilot corpus + reliability) complete & verified — a 30-segment
corpus rated by both models; the Literary-Big-Five structure has real support in the
data. Next up is M3 (coordinate system v1).

### State of the tree

| Area | Where | Status |
|---|---|---|
| API surface | `backend/src/lsap/api/app.py` | `/health`, `/api/axes`, `POST /api/rate`, `/api/segments[/{id}]` live |
| Instrument | `backend/src/lsap/instrument/` | `schema.py` + 30-axis `axes.yaml`; **`rater.py` implemented** (Claude structured output) |
| Persistence | `backend/src/lsap/storage.py` | JSONL ratings + markdown corpus (git-diffable) |
| Corpus & data | `corpus/*.md`, `ratings/*.jsonl`, `reliability/` | 30-segment pilot (`source: pilot`) + 60 ratings + reliability report |
| Coordinates | `backend/src/lsap/coordinates/` | **`reliability.py` implemented** (agreement / correlation / PCA / twins); `projection.py` `CVector` real, `ProjectionModel` stubbed (M3) |
| Engine | `backend/src/lsap/engine/` | `Dials` + `to_bands` real; `operators.yaml` real; `compile_constraints` stubbed (M4) |
| Firewall | `backend/tests/test_firewall.py` | enforced & green (hardened: every import form + `storage`) |
| Frontend | `frontend/src/` | Rater Studio: paste → rate → 30 scored axes + confidence |

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
