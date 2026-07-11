"""Rate the M2 pilot corpus with both raters (Opus 4.8 + Haiku 4.5), concurrently.
Appends one rating per (segment, rater) to `ratings/<id>.jsonl`. Resumable: skips any
(segment, rater) already rated unless --force.

    .venv/Scripts/python.exe scripts/rate_corpus.py [--workers N] [--force]
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

import anthropic

from lsap import storage
from lsap.config import settings
from lsap.instrument import rater
from lsap.instrument.schema import load_axes

RATERS = ["claude-opus-4-8", "claude-haiku-4-5"]


def _client() -> anthropic.Anthropic:
    key = settings.anthropic_api_key
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=key)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    axes = load_axes()
    client = _client()
    segs = [s for s in storage.list_segments() if s.get("source") == "pilot"]
    if not segs:
        raise SystemExit("no pilot segments found — run generate_corpus.py first")

    tasks: list[tuple[str, str]] = []
    for s in segs:
        rated = {r.rater_id for r in storage.load_ratings(s["id"])}
        for model in RATERS:
            if args.force or model not in rated:
                tasks.append((s["id"], model))
    if not tasks:
        print("all pilot segments already rated by both raters; use --force to re-rate")
        return

    print(
        f"rating {len(tasks)} (segment,rater) tasks over {len(segs)} segments "
        f"({args.workers} workers)…",
        flush=True,
    )

    def work(task: tuple[str, str]) -> tuple[str, str, bool]:
        sid, model = task
        seg = storage.load_segment(sid)
        assert seg is not None
        rating = rater.rate(
            segment_id=sid,
            segment_text=seg["text"],
            rater=model,
            axes=axes,
            created_at=datetime.now(UTC).isoformat(),
            client=client,
        )
        storage.save_rating(rating)
        return sid, model, rating.flagged

    done: list[tuple[str, str]] = []
    failed: list[tuple[str, str, str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, t): t for t in tasks}
        for fut in as_completed(futs):
            sid, model = futs[fut]
            try:
                _sid, _m, flagged = fut.result()
                done.append((sid, model))
                print(f"  ok  {sid:22} {model:20}{' FLAGGED' if flagged else ''}", flush=True)
            except Exception as e:  # noqa: BLE001 — report and continue
                failed.append((sid, model, str(e)))
                print(f"  ERR {sid:22} {model:20} {e}", flush=True)

    print(f"\ndone: {len(done)} ok, {len(failed)} failed")
    if failed:
        for sid, model, e in failed:
            print(f"  failed: {sid} {model}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
