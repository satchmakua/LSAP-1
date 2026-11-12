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

    print(f"  consensus panel: {', '.join(model.d.get('raters') or ['(all raters)'])}")

    ranks = model.twin_ranks()
    print("\ntwin-pair check (rank of each segment's twin among all other segments):")
    for r in ranks:
        print(
            f"  rank {r['rank']:>2}  {r['segment_id']:20} twin={r['twin']:20}"
            f" nearest={r['nearest']} d={r['nearest_distance']}"
        )
    if ranks:
        vals = sorted(r["rank"] for r in ranks)
        n = len(vals)
        median = (vals[(n - 1) // 2] + vals[n // 2]) / 2
        print(
            f"\ntwin nearest-neighbour hits: {sum(v == 1 for v in vals)}/{n}"
            f"   twin rank: median {median:g}, mean {sum(vals) / n:.1f}, worst {vals[-1]}"
            f"   in top 3: {sum(v <= 3 for v in vals)}/{n}, top 5: {sum(v <= 5 for v in vals)}/{n}"
            f"   (of {len(model.points) - 1} candidates)"
        )


if __name__ == "__main__":
    main()
