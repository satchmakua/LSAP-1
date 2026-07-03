"""Local-first, git-diffable persistence (DESIGN.md §3).

Ratings are append-only JSONL (one `Rating` per line, so multiple raters/runs accrue in
`ratings/<segment_id>.jsonl`); segments are markdown with YAML frontmatter under
`corpus/<segment_id>.md`. Data lives at the repo root by default; override with the
`LSAP_DATA_DIR` env var (tests point it at a tmp dir).

This module is analysis-side infrastructure — `lsap.engine` must never import it.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from lsap.instrument.schema import Rating

# backend/src/lsap/storage.py -> parents[3] == the repo root (…/LSAP-1)
_REPO_ROOT = Path(__file__).resolve().parents[3]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def data_dir() -> Path:
    return Path(os.environ.get("LSAP_DATA_DIR", str(_REPO_ROOT)))


def ratings_dir() -> Path:
    return data_dir() / "ratings"


def corpus_dir() -> Path:
    return data_dir() / "corpus"


def slugify(title: str, *, fallback: str) -> str:
    slug = _SLUG_RE.sub("-", title.strip().lower()).strip("-")
    return slug or fallback


# ---- ratings (append-only JSONL) ----------------------------------------------------

def save_rating(rating: Rating) -> Path:
    d = ratings_dir()
    d.mkdir(parents=True, exist_ok=True)
    fp = d / f"{rating.segment_id}.jsonl"
    with fp.open("a", encoding="utf-8") as f:
        f.write(rating.model_dump_json() + "\n")
    return fp


def load_ratings(segment_id: str) -> list[Rating]:
    fp = ratings_dir() / f"{segment_id}.jsonl"
    if not fp.exists():
        return []
    out: list[Rating] = []
    for line in fp.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(Rating.model_validate_json(line))
    return out


# ---- corpus (markdown + YAML frontmatter) -------------------------------------------

def save_segment(segment_id: str, text: str, *, source: str, created_at: str) -> Path:
    """Write the segment text once (first rating wins); returns the file path either way."""
    d = corpus_dir()
    d.mkdir(parents=True, exist_ok=True)
    fp = d / f"{segment_id}.md"
    if fp.exists():
        return fp
    front = {
        "id": segment_id,
        "word_count": word_count(text),
        "source": source,
        "created_at": created_at,
    }
    fm = yaml.safe_dump(front, sort_keys=False).strip()
    fp.write_text(f"---\n{fm}\n---\n\n{text.strip()}\n", encoding="utf-8")
    return fp


def load_segment(segment_id: str) -> dict | None:
    fp = corpus_dir() / f"{segment_id}.md"
    if not fp.exists():
        return None
    raw = fp.read_text(encoding="utf-8")
    front, body = _split_frontmatter(raw)
    return {**front, "id": segment_id, "text": body}


def list_segments() -> list[dict]:
    d = corpus_dir()
    if not d.exists():
        return []
    out: list[dict] = []
    for fp in sorted(d.glob("*.md")):
        seg_id = fp.stem
        front, _ = _split_frontmatter(fp.read_text(encoding="utf-8"))
        ratings = load_ratings(seg_id)
        out.append(
            {
                "id": seg_id,
                "word_count": front.get("word_count"),
                "source": front.get("source"),
                "rater_ids": [r.rater_id for r in ratings],
                "rating_count": len(ratings),
            }
        )
    return out


def word_count(text: str) -> int:
    return len(text.split())


def _split_frontmatter(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            front = yaml.safe_load(parts[1]) or {}
            return front, parts[2].lstrip("\n")
    return {}, raw
