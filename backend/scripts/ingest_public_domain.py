"""Ingest public-domain prose segments into the pilot corpus (M6).

Reads a JSON file of segments ({"segments": [{id, author, work, year, source_url,
structural_note, word_count, text}, ...]}) and writes `corpus/<id>.md` with
`source: pilot` + `origin: public-domain` frontmatter, so the analysis loaders include
them while the origin comparison can tell them apart from model-written segments.
Idempotent: skips ids already present (use --force to rewrite).

    .venv/Scripts/python.exe scripts/ingest_public_domain.py segments.json [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lsap import storage


def write_segment(seg: dict, *, force: bool) -> tuple[str, str]:
    d = storage.corpus_dir()
    d.mkdir(parents=True, exist_ok=True)
    fp = d / f"{seg['id']}.md"
    if fp.exists() and not force:
        return seg["id"], "skipped (exists)"
    text = seg["text"].strip()
    wc = len(text.split())
    if not 900 <= wc <= 1500:
        return seg["id"], f"REJECTED (word count {wc} outside 900-1500)"
    front = {
        "id": seg["id"],
        "word_count": wc,
        "source": "pilot",
        "origin": "public-domain",
        "author": seg["author"],
        "work": seg["work"],
        "year": int(seg["year"]),
        "source_url": seg["source_url"],
        "structural_note": seg["structural_note"],
        "created_at": datetime.now(UTC).isoformat(),
    }
    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    fp.write_text(f"---\n{fm}\n---\n\n{text}\n", encoding="utf-8")
    return seg["id"], f"ok ({wc} words)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("segments_json")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    data = json.loads(Path(args.segments_json).read_text(encoding="utf-8"))
    segs = data["segments"] if isinstance(data, dict) else data
    if not segs:
        raise SystemExit("no segments in input")

    rejected = 0
    for seg in segs:
        sid, status = write_segment(seg, force=args.force)
        rejected += status.startswith("REJECTED")
        print(f"  {sid:28} {status}")
    print(f"\ndone: {len(segs) - rejected} written/kept, {rejected} rejected")
    if rejected:
        sys.exit(1)


if __name__ == "__main__":
    main()
