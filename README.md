# LSAP-1

**A tool that measures how a piece of fiction is built — and a writing engine you steer with dials instead of by imitating an author.**

## What it is

People describe writing with words like "lyrical," "spare," or "dreamlike," but those
words are vague and two readers rarely mean the same thing by them. LSAP-1 tries to make
those descriptions concrete and repeatable.

You give it a scene of fiction — roughly 1,000 to 3,000 words. It scores the passage on
**30 specific traits**, each on a scale of 1 to 7. For example:

- how plain or rare the words are,
- how much actually happens,
- how far inside a character's head the telling goes,
- whether the story's world stays stable or keeps shifting,
- whether the mood is dark or bright, steady or swinging.

Each trait comes with written definitions of what a 1, a 4, and a 7 look like, so a score
means the same thing every time. An AI model does the scoring by following that written
manual. Every passage in the project's test collection has been scored by two different
models, so the two can be checked against each other.

It never judges whether writing is *good*. It only records what is *there*.

## What you can do with it

1. **Measure a passage.** Paste in a scene and get its 30 scores back, each with a note
   of how confident the scorer was.
2. **See where it sits.** Thirty numbers are a lot to hold in your head, so the tool boils
   them down to a few underlying dimensions and places each passage as a dot on a map.
   Passages built alike land near each other: a bare, camera-like scene sits far from a
   dense, dreamlike, inward one. A new passage appears beside the ones it most resembles.
3. **Write by dials.** The other half of the tool works in reverse. Instead of asking for
   "a scene in the style of" some author, you set five sliders — plain to dense, told in
   order to fragmented, outside a character to deep inside one, a stable world to an
   unstable one, calm to intense — give it a situation, and it writes the scene a
   paragraph at a time. You can then send the result back through the measuring side to
   check that the sliders did what they claim. (Moving the first slider from low to high
   took the average sentence from 6 words to 140.)
4. **Score a passage yourself.** A hand-scoring mode lets a person rate a passage against
   the same manual, without seeing what the models said, so human and machine readings
   can be compared.

## How it keeps itself honest

- **Measuring and writing are walled off.** The writing engine is never allowed to see
  the scores or the map. The measuring side can test the engine, but the engine cannot
  learn to game the measurements. An automated test enforces the wall.
- **Disagreement is reported, not hidden.** When the scorers disagree about a trait, that
  is recorded as a finding about the trait rather than smoothed away.
- **The map admits what it misses.** Its few dimensions capture about 70% of the
  differences between passages; the other 29% is reported every time instead of being
  quietly dropped.
- **Mistakes are corrected in the open.** When I found errors in results I had already
  published, I wrote up what was wrong and what the data actually says — see
  [docs/reliability-notes.md](docs/reliability-notes.md).
- **No imitation, no detection.** It does not copy named writers, and it is not a tool for
  guessing who wrote something.

## Where it stands

The measuring side, the map, and the writing engine all work. The test collection is 100
passages: 85 written by an AI model to detailed specifications, and 15 public-domain
classics (Austen, Twain, Woolf, Joyce and others) as a check. Of the 30 traits, 26 are
scored consistently by the two models; four are not yet — how rare the words are, which
emotion dominates, how clear cause and effect are, and plot versus experience.

The biggest open question is what the map really describes. It fits the 85 generated
passages noticeably better than the 15 classics, so part of its shape may come from how
the generated passages were written rather than from fiction in general. Adding much more
human-written prose is the clear next step. The human-versus-machine comparison is built,
but so far only one passage has been scored by hand.

## Technical summary

LSAP-1 is the first buildable version of the **Literary Space Annotation Protocol**: an
honest measurement *instrument* that turns a prose segment into 30 anchored numbers and a
5–6 dimension coordinate space (the "C-space" — the map above), plus a stateful
*generative engine* that writes prose by dialing structural parameters rather than
imitating named authors. The two halves share a vocabulary but are architecturally
forbidden from feeding each other (the Charter's analysis↔generation firewall).

**Stack:** Python 3.11+ (FastAPI · Pydantic v2 · scikit-learn · Claude via the `anthropic` SDK) · React 19 + TypeScript (Vite 8) · local-first, git-diffable files (markdown corpus, YAML defs, JSONL ratings).

**Status: v1 slice (M0–M4) complete; Phase 4 hardening — M5 and M6 done; M7's human-rater mode is built, with one hand-scored segment so far (the human↔model comparison needs at least eight).** Rate a segment on 30 anchored axes → watch it land in a fitted C-space beside its nearest kin → dial the operators and generate measurably different prose, with the analysis/generation firewall intact.

- **Corpus:** **100 segments** — 85 written by Claude to structural briefs (never by author imitation) plus **15 public-domain** passages as a non-model control, each verified verbatim against its source.
- **Instrument:** 30 anchored axes (registry **version 3**), Claude-rated under a frozen manual; ratings carry an `axes_version` and anchor cohorts are never pooled. **26 of 30 axes** clear the reliability bar. M5 re-anchored the two ambiguous axes: L3 fixed (within-1 **0.40 → 0.87**); L1 resisted two revisions (0.52 on the wider corpus) and its future is an open question. A **human scoring mode** lets a person rate against the same manual, blind; one segment has been hand-scored so far.
- **Coordinates:** 5 locked factors over 100 segments, **70.9% explained, C6 residual 29.1%**. Two honest headlines from M6: **the pilot's factor structure was substantially an n=30 artifact** (PC1 44.8% → 33.8%; 80% now needs 8 components, not 6), though the factors are far **more reproducible** than the pilot could know (split-half loading stability **0.505 → 0.679**); and **the structure is partly a property of the generated corpus** — out of sample, factors fitted on model-written prose capture 66% of the variance in held-out model-written segments but only 52% in the public-domain passages. Every twin pair lands in its partner's top 5 of 100.
- **Engine:** operators → rules → a stateful WS/PL/MF/EF/LR loop. Moving compression 0.05 → 0.95 took mean sentence length **6.3 → 140.5 words** and moved **4/4** predicted instrument axes up (Syntactic Depth 1→7).

See [docs/reliability-notes.md](docs/reliability-notes.md) for what these numbers mean, how they are computed, and two corrections to earlier results; the live figures are in `reliability/report.md` and `coordinates/model.json`.

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
  nearest neighbours. *Human scoring*: read a corpus segment beside the 30 axes and
  hand-score it against the visible anchors, stored as `human:<name>` for human↔model
  comparison. Scoring is blind — segments appear under neutral codes and no model score is
  shown — and a half-finished segment is kept as a draft.
- **Engine** — dial the five operators (or pick a preset), give a situation, and generate;
  each paragraph shows its scene phase, language register, emotional energy and memory
  field. "Re-rate this output" sends the prose back through the instrument — one-way.

The API is at **http://localhost:8000** (`/health`, `/api/axes`, `POST /api/rate`,
`POST /api/rate/manual`, `/api/segments`, `/api/cspace`, `/api/segments/{id}/projection`,
`/api/presets`, `POST /api/generate`).

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
- **[LSAP_Foundational_Blueprint.md](docs/LSAP_Foundational_Blueprint.md)** — the domain theory (the L0–L7 stack and the Epistemic Charter).
- **[docs/adr/](docs/adr/)** — architecture decision records, including the [analysis/generation firewall](docs/adr/0002-analysis-generation-firewall.md).

## Layout

```
backend/   FastAPI + Pydantic — instrument (L1) · coordinates (L2/L3) · engine (L6) · api
frontend/  React 19 + Vite — Rater Studio · C-Space Map · Engine Console
docs/      ADRs and long-form notes
```
