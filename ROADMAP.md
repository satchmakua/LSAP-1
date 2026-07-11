# ROADMAP — LSAP-1

The milestone checklist — build the next unchecked milestone in order. Full rationale is
in [DESIGN.md](DESIGN.md); the domain theory is in
[LSAP_Foundational_Blueprint.md](LSAP_Foundational_Blueprint.md).

**Rules of the road:**
- Each milestone is an **independently runnable** slice — something actually testable end-to-end.
- Every milestone ends with explicit **Test** steps — the acceptance criteria.
- Build **top-down**: deepen the same vertical slice (rate → project → generate).
- Check a box **only after its Test passes**, then add a
  `PROGRESS.md` entry.
- The **firewall** (`backend/tests/test_firewall.py`) must stay green at every milestone.

---

## Phase 0 — Walking skeleton

- [x] **M0 — Skeleton & it runs.** Hybrid monorepo: FastAPI backend serving `/health`
  and `/api/axes` (the 30-axis registry loaded from `axes.yaml`), React 19 + Vite
  frontend rendering the axes grouped by field (the Rater Studio seed), the Charter-P4
  firewall test, and pytest + Vitest green.
  **Test:** `npm test` → backend (7) and frontend tests pass; `npm run dev` → backend
  on `:8000` (`/health` returns `axes_loaded: 30`), frontend on `:5173` lists all 30
  axes across six fields with A3/A5/S5 tagged "forced choice";
  `cd backend && uv run pytest -k firewall` is green.

## Phase 1 — The instrument (L1)

- [x] **M1 — Instrument, one segment end-to-end.** `instrument/rater.py` (Claude
  structured output → validated `Rating`), persistence to `ratings/*.jsonl` +
  `corpus/*.md`, `POST /api/rate`, and the Rater Studio "Rate" panel (30 scores with
  per-axis confidence and the `flagged` state).
  **Test:** paste a ~1–2k-word passage → click Rate → 30 scores + confidence render;
  the rating is written to `ratings/<segment>.jsonl`; re-running yields a comparable
  rating. **✓ verified 2026-07-03** — a live Opus 4.8 rating of an original 1,135-word
  scene produced a coherent, defensible 30-axis reading (grief / unresolved / poetic;
  single-voice deep interiority; near-static event density), persisted, and appended a
  second rating on re-run.

- [ ] **M2 — Pilot corpus + reliability.** Assemble the 30-segment corpus under
  `corpus/` (with deliberate redundant pairs); run both raters (`claude-opus-4-8` +
  `claude-haiku-4-5`); `coordinates/reliability.py` computes inter-rater agreement, the
  30×30 correlation matrix, and a first PCA.
  **Test:** run the reliability script → it prints per-axis agreement, the correlation
  matrix, and explained variance; you can state which axes are reliable, redundant, or
  ambiguous — with numbers.

## Phase 2 — Coordinate system (L2/L3)

- [ ] **M3 — Coordinate system v1.** Fit + persist the PCA (`coordinates/model.json`);
  add a project endpoint; build the C-Space Map (scatter + nearest neighbors +
  trajectory) in the frontend.
  **Test:** submit a new segment → it appears as a dot in C-space with nearest
  neighbors that read as sensible; explained variance per factor is shown.

## Phase 3 — The engine (L6)

- [ ] **M4 — Generative Engine MVP.** Flesh out `engine/compiler.py` (band-normalizer +
  constraint compiler), the story state machine, and runtime cognition
  (WS/PL/MF/EF/LR); stream generation; add presets; build the Engine Console with five
  sliders, a live state panel, and the one-way "re-rate output" crossing.
  **Test:** move one slider low→high and Generate twice → the prose is legibly
  different across both runs; the state panel updates per paragraph; "re-rate output"
  shows the instrument scores shifting in the intended direction.

---

**North star:** paste a scene → watch it become 30 numbers and a point in C-space;
push a slider → watch the prose change character. Instrument honest, engine
controllable, wall intact.

_v2+ (out of this slice): L4 interpretation tensor · L5 archetype/phase-transition
classifier · L7 multi-agent simulation · the Work-Description combinator (D3)._
