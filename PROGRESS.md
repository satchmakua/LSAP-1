# PROGRESS — LSAP-1

A build log of what shipped and the notable decisions behind it. **Keep it honest** —
this is the working memory between build sessions. The forward-looking plan and
acceptance tests live in [ROADMAP.md](ROADMAP.md); this is the "what got done and why"
companion.

**Current phase:** M1 (the rater) built, reviewed, and self-verified — awaiting the
human's live rating test (needs `ANTHROPIC_API_KEY`).

### State of the tree

| Area | Where | Status |
|---|---|---|
| API surface | `backend/src/lsap/api/app.py` | `/health`, `/api/axes`, `POST /api/rate`, `/api/segments[/{id}]` live |
| Instrument | `backend/src/lsap/instrument/` | `schema.py` + 30-axis `axes.yaml`; **`rater.py` implemented** (Claude structured output) |
| Persistence | `backend/src/lsap/storage.py` | JSONL ratings + markdown corpus (git-diffable) |
| Coordinates | `backend/src/lsap/coordinates/projection.py` | `CVector` real; `ProjectionModel` stubbed (M3) |
| Engine | `backend/src/lsap/engine/` | `Dials` + `to_bands` real; `operators.yaml` real; `compile_constraints` stubbed (M4) |
| Firewall | `backend/tests/test_firewall.py` | enforced & green (hardened: every import form + `storage`) |
| Frontend | `frontend/src/` | Rater Studio: paste → rate → 30 scored axes + confidence |

---

## M1 — The rater · built 2026-07-03 · awaiting live test

Implemented the L1 instrument end-to-end: a prose segment → a validated 30-axis `Rating`
via Claude structured output, persisted and read back.

**Shipped**
- **Rater** (`instrument/rater.py`): builds a *dynamic* Pydantic output model — one
  required field per axis, `value` a `Literal` int-enum (1–7) for scalar axes and a
  `Literal` string-enum for forced-choice — so structured-output constrained decoding
  guarantees all 30 axes are present and in range. The manual (golden rules + every
  axis's anchors/choices/watch-fors) is the cached system prompt; adaptive thinking is
  gated to Opus-class models (Haiku 4.5 supports neither adaptive thinking nor effort).
  `to_rating` stores forced-choice values as the 1-based index into `choices`.
- **Persistence** (`storage.py`): append-only `ratings/<id>.jsonl` (raters/runs accrue)
  + write-once `corpus/<id>.md` with YAML frontmatter. Repo-root default, `LSAP_DATA_DIR`
  override for tests.
- **API**: `POST /api/rate` (derives a stable segment id, stamps `created_at`, rejects a
  paid rating that would be mis-attributed — see the fix below), `GET /api/segments`,
  `GET /api/segments/{id}`.
- **Frontend**: the Rater Studio rate form (textarea + title + rater picker + word-count
  hint) and a `ScoresView` that renders the 30 scores grouped by field with a value bar,
  forced-choice label, confidence dots, and a flagged banner.

**Decisions & the current API, verified against live docs + the installed SDK**
- `client.messages.parse(output_format=<model>, system=, thinking=)` on **anthropic
  0.116.0** — confirmed via `inspect.signature`; the dynamic schema passes the SDK's
  `transform_schema` (A3 → 8-value string enum, L1 → int enum 1–7, all 30 required).
- `claude-opus-4-8` canonical rater (adaptive thinking); `claude-haiku-4-5` second rater
  (no thinking). No `temperature`/`top_p` (400 on Opus 4.8).

**Reviewed** — a single adversarial reviewer agent (the parallel multi-agent workflow was
blocked by transient server-side rate limits) confirmed the forced-choice indexing,
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
- `uv run pytest` → **28 passed** (rater schema/conversion/thinking-gating, storage
  round-trips, endpoint incl. the 409 guard and rerun-append, firewall scanner). `ruff`
  clean. Frontend `vitest` → **2 passed** (renders scores from a mocked rating incl. the
  forced-choice label); `build` + `oxlint` clean.
- The live rating (real Claude call) is the human's Test step — set `ANTHROPIC_API_KEY`
  in `backend/.env`, then paste a ~1–2k-word passage in the Rater Studio.

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
