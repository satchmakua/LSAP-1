"""A/B one dial: generate at low and at high, then re-rate both through the instrument.

This is the sanctioned one-way crossing (Charter P4): generated prose is measured
*offline*, and the measurement never feeds back into generation. The engine package
itself still imports nothing from the analysis side — only this script sees both.

    .venv/Scripts/python.exe scripts/engine_ab.py --dial c1 --paragraphs 4
"""

from __future__ import annotations

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import anthropic

from lsap.config import settings
from lsap.engine.compiler import Dials
from lsap.engine.runtime import GenerationRun, generate
from lsap.instrument import rater
from lsap.instrument.schema import load_axes

# Axes each dial is *supposed* to move, for a directional check.
EXPECTED: dict[str, list[str]] = {
    "c1": ["L2", "L3", "S4", "L1"],   # compression -> syntax, density, figuration
    "c2": ["N2", "N4"],               # temporal structure -> linearity, time behaviour
    "c3": ["C1", "C3", "C5"],         # interiorization -> distance, transparency, interior
    "c4": ["P1", "P2"],               # (de)stabilization -> ontology, epistemics
    "c5": ["A2", "A4"],               # affect -> volatility, intensity
}


def _client() -> anthropic.Anthropic:
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def prose_stats(run: GenerationRun) -> dict:
    text = " ".join(p.text for p in run.paragraphs)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    words = text.split()
    return {
        "words": len(words),
        "sentences": len(sentences),
        "mean_sentence_words": round(len(words) / max(1, len(sentences)), 1),
    }


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--dial", default="c1", choices=sorted(EXPECTED))
    ap.add_argument("--low", type=float, default=0.05)
    ap.add_argument("--high", type=float, default=0.95)
    ap.add_argument("--paragraphs", type=int, default=4)
    ap.add_argument(
        "--situation",
        default="A man returns to an apartment he has not visited in months.",
    )
    args = ap.parse_args()

    axes = load_axes()
    client = _client()
    base = {"c1": 0.4, "c2": 0.4, "c3": 0.4, "c4": 0.4, "c5": 0.4}

    def run_one(level: float) -> GenerationRun:
        dials = Dials(**{**base, args.dial: level})
        return generate(
            dials=dials, situation=args.situation, paragraphs=args.paragraphs,
            client=client, model=settings.renderer_model,
        )

    print(f"generating A ({args.dial}={args.low}) and B ({args.dial}={args.high})…", flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        fa, fb = ex.submit(run_one, args.low), ex.submit(run_one, args.high)
        run_a, run_b = fa.result(), fb.result()

    for tag, run in (("A(low)", run_a), ("B(high)", run_b)):
        s = prose_stats(run)
        print(f"\n=== {tag} {args.dial} — {s['words']} words, "
              f"mean sentence {s['mean_sentence_words']} words ===")
        print(f"  phases:    {[p.phase for p in run.paragraphs]}")
        print(f"  registers: {[p.language_register for p in run.paragraphs]}")
        print(f"  energy:    {[p.emotional_energy for p in run.paragraphs]}")
        print(f"\n  first paragraph:\n  {run.paragraphs[0].text[:420]}")

    print("\nre-rating both through the instrument (one-way)…", flush=True)
    now = datetime.now(UTC).isoformat()

    def rate_one(tag_run):
        tag, run = tag_run
        text = "\n\n".join(p.text for p in run.paragraphs)
        return tag, rater.rate(
            segment_id=f"engine-ab-{tag}", segment_text=text, rater=settings.rater_model,
            axes=axes, created_at=now, client=client,
        )

    with ThreadPoolExecutor(max_workers=2) as ex:
        rated = dict(ex.map(rate_one, [("A", run_a), ("B", run_b)]))

    a = {s.axis_id: s.value for s in rated["A"].scores}
    b = {s.axis_id: s.value for s in rated["B"].scores}
    names = {ax.id: ax.name for ax in axes}

    print(f"\n=== instrument deltas (B[{args.high}] - A[{args.low}]) ===")
    expected = EXPECTED[args.dial]
    for aid in expected:
        d = b[aid] - a[aid]
        mark = "OK  " if d > 0 else ("--  " if d == 0 else "DOWN")
        print(f"  {mark} {aid:3} {names[aid]:26} A={a[aid]} B={b[aid]}  delta={d:+d}")
    moved = sum(1 for aid in expected if b[aid] - a[aid] > 0)
    print(f"\n  expected axes that rose: {moved}/{len(expected)}")

    others = sorted(
        ((abs(b[k] - a[k]), k) for k in a if k not in expected), reverse=True
    )[:5]
    print("  largest other shifts: " + ", ".join(
        f"{k}({b[k] - a[k]:+d})" for _, k in others
    ))


if __name__ == "__main__":
    main()
