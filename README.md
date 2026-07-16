# LSAP-1

**One coordinate system for reading prose, one controllable engine for writing it — with a hard wall between them.**

LSAP-1 is the first buildable version of the **Literary Space Annotation Protocol**: an
honest measurement *instrument* that turns a prose segment into 30 anchored numbers and a
5–6 dimension coordinate space, plus a stateful *generative engine* that writes prose by
dialing structural parameters rather than imitating named authors. The two halves share a
vocabulary but are architecturally forbidden from feeding each other (the Charter's
analysis↔generation firewall).

**Stack:** Python 3.11+ (FastAPI · Pydantic v2 · scikit-learn · Claude via the `anthropic` SDK) · React 19 + TypeScript (Vite 8) · local-first, git-diffable files (markdown corpus, YAML defs, JSONL ratings).

**Status:** **M2 (pilot corpus + reliability) complete & verified** — a 30-segment corpus rated by both models; the reliability run shows the Literary-Big-Five structure has real support (PC1 ≈ 45% of variance, ~6 factors cover 80%). See [PROGRESS.md](PROGRESS.md) and `reliability/report.md`. Next milestone: coordinate system v1 (M3).

## Run it

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/) on your PATH, Node ≥ 20.19, npm. For M1+ features, copy `.env.example` to `backend/.env` and add your `ANTHROPIC_API_KEY`.

```bash
npm run setup   # once — backend `uv sync` + frontend `npm install`
npm run dev     # backend (:8000) + frontend (:5173, proxies /api → backend)
npm test        # backend pytest + frontend vitest
npm run lint    # ruff + oxlint
npm run build   # frontend production build
```

Open **http://localhost:5173** for the Rater Studio: paste a ~1–3k-word passage, pick a
rater, and score it on all 30 axes. The API is at **http://localhost:8000**
(`/health`, `/api/axes`, `POST /api/rate`, `/api/segments`).

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
