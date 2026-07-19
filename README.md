# LSAP-1

**One coordinate system for reading prose, one controllable engine for writing it — with a hard wall between them.**

LSAP-1 is the first buildable version of the **Literary Space Annotation Protocol**: an
honest measurement *instrument* that turns a prose segment into 30 anchored numbers and a
5–6 dimension coordinate space, plus a stateful *generative engine* that writes prose by
dialing structural parameters rather than imitating named authors. The two halves share a
vocabulary but are architecturally forbidden from feeding each other (the Charter's
analysis↔generation firewall).

**Stack:** Python 3.11+ (FastAPI · Pydantic v2 · scikit-learn · Claude via the `anthropic` SDK) · React 19 + TypeScript (Vite 8) · local-first, git-diffable files (markdown corpus, YAML defs, JSONL ratings).

**Status:** **M3 (coordinate system v1) complete & verified** — rate a segment on 30 anchored axes, then watch it land in a fitted C-space next to its nearest kin. The projection over the 30-segment pilot corpus locks 5 factors (79.4% explained, C6 residual 20.6%); a new minimalist passage projects nearest the corpus's minimalist twins. See [PROGRESS.md](PROGRESS.md), `reliability/report.md`, `coordinates/model.json`. Next milestone: the generative engine MVP (M4).

## Run it

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/) on your PATH, Node ≥ 20.19, npm. For M1+ features, copy `.env.example` to `backend/.env` and add your `ANTHROPIC_API_KEY`.

```bash
npm run setup   # once — backend `uv sync` + frontend `npm install`
npm run dev     # backend (:8000) + frontend (:5173, proxies /api → backend)
npm test        # backend pytest + frontend vitest
npm run lint    # ruff + oxlint
npm run build   # frontend production build
```

Open **http://localhost:5173**: paste a ~1–3k-word passage, pick a rater, and score it on
all 30 axes — then see it placed in the **C-Space Map** beside its nearest neighbours.
The API is at **http://localhost:8000** (`/health`, `/api/axes`, `POST /api/rate`,
`/api/segments`, `/api/cspace`, `/api/segments/{id}/projection`).

Operational runners (from `backend/`, needing `ANTHROPIC_API_KEY`):

```bash
uv run python scripts/generate_corpus.py     # write the pilot corpus (idempotent)
uv run python scripts/rate_corpus.py         # rate it with both raters (resumable)
uv run python -m lsap.coordinates.reliability  # agreement / correlation / PCA report
uv run python scripts/fit_projection.py      # fit + persist coordinates/model.json
```

## Docs

- **[DESIGN.md](DESIGN.md)** — the engineering spec: stack, data contracts, architecture, milestones.
- **[ROADMAP.md](ROADMAP.md)** — the milestone checklist (M0 done; M1–M4 next).
- **[PROGRESS.md](PROGRESS.md)** — the build log.
- **[LSAP_Foundational_Blueprint.md](docs/LSAP_Foundational_Blueprint.md)** — the domain theory (the L0–L7 stack and the Epistemic Charter).
- **[docs/adr/](docs/adr/)** — architecture decision records, including the [analysis/generation firewall](docs/adr/0002-analysis-generation-firewall.md).

## Layout

```
backend/   FastAPI + Pydantic — instrument (L1) · coordinates (L2/L3) · engine (L6) · api
frontend/  React 19 + Vite — Rater Studio · (C-Space Map, Engine Console to come)
docs/      ADRs and long-form notes
```
