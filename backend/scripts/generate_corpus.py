"""Generate the M2 pilot corpus: one original ~1,200-word segment per spec, spanning the
axis contrast space, each written by Claude to a purely structural brief (no author
imitation — Charter P7). Writes `corpus/<id>.md` with `source: pilot` frontmatter.
Idempotent: skips segments already present (use --force to regenerate).

    .venv/Scripts/python.exe scripts/generate_corpus.py [--workers N] [--only a,b] [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import anthropic
import yaml

from lsap import storage
from lsap.config import settings

SPECS = Path(__file__).parent / "corpus_specs.json"
MODEL = "claude-opus-4-8"

SYSTEM = (
    "You write original literary prose to a precise structural brief. "
    "Do not imitate, reference, or evoke any named author or existing work. "
    "Output ONLY the prose — no title, no preamble, no notes, no markdown headings or "
    "frontmatter. Write in coherent paragraphs."
)


def _client() -> anthropic.Anthropic:
    key = settings.anthropic_api_key
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=key)


def generate_one(client: anthropic.Anthropic, spec: dict) -> str:
    prompt = (
        f"Target structural profile:\n{spec['profile']}\n\n"
        f"Situation to write:\n{spec['situation']}\n\n"
        "Write roughly 1,100–1,300 words of original literary prose that strongly and "
        "deliberately exhibits the target profile — make the structural qualities "
        "unmistakable. Output only the prose."
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def write_segment(spec: dict, text: str) -> Path:
    d = storage.corpus_dir()
    d.mkdir(parents=True, exist_ok=True)
    front = {
        "id": spec["id"],
        "word_count": len(text.split()),
        "source": "pilot",
        "profile": spec["profile"],
        "situation": spec["situation"],
        "pair": spec["pair"],
        "created_at": datetime.now(UTC).isoformat(),
    }
    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).strip()
    fp = d / f"{spec['id']}.md"
    fp.write_text(f"---\n{fm}\n---\n\n{text}\n", encoding="utf-8")
    return fp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    if args.only:
        want = set(args.only.split(","))
        specs = [s for s in specs if s["id"] in want]
    if not args.force:
        specs = [s for s in specs if not (storage.corpus_dir() / f"{s['id']}.md").exists()]
    if not specs:
        print("nothing to generate (all present); use --force to regenerate")
        return

    print(f"generating {len(specs)} segments with {MODEL} ({args.workers} workers)…", flush=True)
    client = _client()

    def work(spec: dict) -> tuple[str, int, Path]:
        text = generate_one(client, spec)
        fp = write_segment(spec, text)
        return spec["id"], len(text.split()), fp

    done: list[tuple[str, int]] = []
    failed: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, s): s["id"] for s in specs}
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                _id, wc, _fp = fut.result()
                done.append((_id, wc))
                print(f"  ok  {_id:22} {wc} words", flush=True)
            except Exception as e:  # noqa: BLE001 — report and continue
                failed.append((sid, str(e)))
                print(f"  ERR {sid:22} {e}", flush=True)

    print(f"\ndone: {len(done)} ok, {len(failed)} failed")
    if failed:
        for sid, e in failed:
            print(f"  failed: {sid}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
