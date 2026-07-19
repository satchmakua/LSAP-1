"""Fit the C-space projection over the rated pilot corpus, persist it, and sanity-check it.

The check is the M3 acceptance criterion made objective: the 4 redundant twin-pairs
(same structural profile, different scene) should come out as each other's nearest
neighbour in C-space.

    .venv/Scripts/python.exe scripts/fit_projection.py
"""

from __future__ import annotations

import sys

from lsap.coordinates.projection import fit_from_storage


def main() -> None:
    try:  # Windows consoles default to cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

    model = fit_from_storage()
    path = model.save()
    print(f"fitted over {model.d['n_segments']} segments -> {path}\n")

    for f in model.factors:
        print(f"  {f['id']}  {f['explained_variance'] * 100:5.1f}%  {f['label']}")
        print("        top: " + ", ".join(f"{a}({w:+.2f})" for a, w in f["top_axes"]))
    total_ev = sum(f["explained_variance"] for f in model.factors)
    print(
        f"\n  {len(model.factors)} factors explain {total_ev * 100:.1f}%"
        f"   C6 residual {model.residual * 100:.1f}%"
    )

    groups: dict[str, list[dict]] = {}
    for p in model.points:
        if p.get("pair"):
            groups.setdefault(p["pair"], []).append(p)

    print("\ntwin-pair nearest-neighbour check:")
    hits = total = 0
    for _group, members in sorted(groups.items()):
        if len(members) != 2:
            continue
        for p in members:
            total += 1
            twin = next(m["segment_id"] for m in members if m["segment_id"] != p["segment_id"])
            nn = model.neighbors(p["scores"], k=1, exclude=p["segment_id"])[0]
            ok = nn.segment_id == twin
            hits += int(ok)
            print(
                f"  {'OK  ' if ok else 'MISS'} {p['segment_id']:20} nearest={nn.segment_id:20}"
                f" (twin={twin}) d={nn.distance}"
            )
    print(f"\ntwin nearest-neighbour hits: {hits}/{total}")


if __name__ == "__main__":
    main()
