# LSAP-1

**One coordinate system for reading prose, one controllable engine for writing it — with a hard wall between them.**

LSAP-1 is the first buildable version of the **Literary Space Annotation Protocol**: an
honest measurement *instrument* that turns a prose segment into 30 anchored numbers and a
5–6 dimension coordinate space, plus a stateful *generative engine* that writes prose by
dialing structural parameters rather than imitating named authors. The two halves share a
vocabulary but are architecturally forbidden from feeding each other (the Charter's
analysis↔generation firewall).

**Stack:** Python 3.11+ (FastAPI · Pydantic v2 · scikit-learn · Claude via the `anthropic` SDK) · React 19 + TypeScript (Vite 8) · local-first, git-diffable files (markdown corpus, YAML defs, JSONL ratings).

**Status: v1 slice (M0–M4) complete; Phase 4 hardening — M5 and M6 done, M7's human-rater mode built and awaiting hand-scoring.** Rate a segment on 30 anchored axes → watch it land in a fitted C-space beside its nearest kin → dial the operators and generate measurably different prose, with the analysis/generation firewall intact.

- **Corpus:** **100 segments** — 85 written by Claude to structural briefs (never by author imitation) plus **15 public-domain** passages as a non-model control, each verified verbatim against its source.
- **Instrument:** 30 anchored axes (registry **version 3**), Claude-rated under a frozen manual; ratings carry an `axes_version` and anchor cohorts are never pooled. M5 re-anchored the two ambiguous axes: L3 fixed (within-1 **0.40 → 0.87**); L1 resisted two revisions but recovered to 0.52 on the wider corpus and remains a split candidate.
- **Coordinates:** 5 locked factors over 100 segments, **70.9% explained, C6 residual 29.1%**. M6's honest headline: **the pilot's factor structure was substantially an n=30 artifact** (PC1 44.8% → 33.8%; 80% now needs 8 components, not 6) — but the factors are far **more reproducible** than the pilot could know (split-half loading stability **0.505 → 0.679**) and are **not a generator artifact** (public-domain prose loads the same structure, |r| 0.95–0.999). Every twin pair lands in its partner's top 5 of 100.
- **Engine:** operators → rules → a stateful WS/PL/MF/EF/LR loop. Moving compression 0.05 → 0.95 took mean sentence length **6.3 → 140.5 words** and moved **4/4** predicted instrument axes up (Syntactic Depth 1→7).

See [PROGRESS.md](PROGRESS.md), `reliability/report.md`, `coordinates/model.json`.

## Run it

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/) on your PATH, Node ≥ 20.19, npm. For M1+ features, copy `.env.example` to `backend/.env` and add your `ANTHROPIC_API_KEY`.

```bash
npm run setup   # once — backend `uv sync` + frontend `npm install`
npm run dev     # backend (:8000) + frontend (:5173, proxies /api → backend)
npm test        # backend pytest + frontend vitest
npm run lint    # ruff + oxlint
npm run build   # frontend production build
```

Open **http://localhost:5173** — two tabs:

- **Instrument** — two modes. *Model rating*: paste a ~1–3k-word passage, pick a model
  rater, score it on all 30 axes, and see it placed in the **C-Space Map** beside its
  nearest neighbours. *Human scoring*: pick a corpus segment and hand-score it against the
  visible anchors, stored as `human:<name>` for human↔model comparison.
- **Engine** — dial the five operators (or pick a preset), give a situation, and generate;
  each paragraph shows its scene phase, language register, emotional energy and memory
  field. "Re-rate this output" sends the prose back through the instrument — one-way.

The API is at **http://localhost:8000** (`/health`, `/api/axes`, `POST /api/rate`,
`/api/segments`, `/api/cspace`, `/api/segments/{id}/projection`, `/api/presets`,
`POST /api/generate`).

Operational runners (from `backend/`, needing `ANTHROPIC_API_KEY`):

```bash
uv run python scripts/generate_corpus.py       # write the pilot corpus (idempotent)
uv run python scripts/ingest_public_domain.py segments.json   # add non-model control segments
uv run python scripts/rate_corpus.py           # rate it with both raters (resumable)
uv run python -m lsap.coordinates.reliability  # agreement / correlation / PCA report
uv run python scripts/fit_projection.py        # fit + persist coordinates/model.json
uv run python scripts/engine_ab.py --dial c1   # A/B a dial, then re-rate both runs
```

## Docs

- **[DESIGN.md](DESIGN.md)** — the engineering spec: stack, data contracts, architecture, milestones.
- **[ROADMAP.md](ROADMAP.md)** — the milestone checklist (M0–M6 done; M7 adds a human rater, then the v2 layers).
- **[PROGRESS.md](PROGRESS.md)** — the build log.
- **[LSAP_Foundational_Blueprint.md](docs/LSAP_Foundational_Blueprint.md)** — the domain theory (the L0–L7 stack and the Epistemic Charter).
- **[docs/adr/](docs/adr/)** — architecture decision records, including the [analysis/generation firewall](docs/adr/0002-analysis-generation-firewall.md).

## Layout

```
backend/   FastAPI + Pydantic — instrument (L1) · coordinates (L2/L3) · engine (L6) · api
frontend/  React 19 + Vite — Rater Studio · C-Space Map · Engine Console
docs/      ADRs and long-form notes
```
