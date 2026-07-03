# PROGRESS — LSAP-1

A build log of what shipped and the notable decisions behind it. **Keep it honest** —
this is the working memory between build sessions. The forward-looking plan and
acceptance tests live in [ROADMAP.md](ROADMAP.md); this is the "what got done and why"
companion.

**Current phase:** M0 shipped & verified — next up is M1 (the rater).

### State of the tree

| Area | Where | Status |
|---|---|---|
| API surface | `backend/src/lsap/api/app.py` | `/health`, `/api/axes` live |
| Instrument schema + registry | `backend/src/lsap/instrument/` | `schema.py` + 30-axis `axes.yaml` real; `rater.py` stubbed (M1) |
| Coordinates | `backend/src/lsap/coordinates/projection.py` | `CVector` real; `ProjectionModel` stubbed (M3) |
| Engine | `backend/src/lsap/engine/` | `Dials` + `to_bands` real; `operators.yaml` real; `compile_constraints` stubbed (M4) |
| Firewall | `backend/tests/test_firewall.py` | enforced & green |
| Frontend | `frontend/src/` | Rater Studio seed (axes grouped by field) |

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
