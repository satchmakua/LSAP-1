"""M2 reliability analysis over the rated pilot corpus (blueprint Phase 2, DESIGN §6.2).

Reads every pilot segment's ratings from storage and reports, with numbers:
  - per-axis inter-rater (model↔model) agreement and mean confidence,
  - the axis correlation matrix over the scalar axes (redundancy → merge candidates),
  - PCA over the scalar axes (does a small latent-factor structure emerge?),
  - twin-pair consistency (do equivalent-profile segments land near each other?).

This is the honest moment: the framework either crystallizes or reveals a more
interesting shape — either outcome passes (Charter P1/P3). Forced-choice axes (A3/A5/S5)
are analysed by agreement/distribution, not folded into the scalar PCA — with n≈30
one-hot encoding (DESIGN §4.2) would be degenerate; M3 locks the projection.

`coordinates/` may read `instrument` + `storage`; never the reverse (the firewall).
"""

from __future__ import annotations

import json
import sys

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import cohen_kappa_score
from sklearn.preprocessing import StandardScaler

from lsap import storage
from lsap.instrument.schema import AxisDef, load_axes, load_axes_version

# ---- pure metrics (unit-tested offline) --------------------------------------------


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rho = Pearson on ranks. Returns 0.0 when either side is constant."""
    ar = np.argsort(np.argsort(a)).astype(float)
    br = np.argsort(np.argsort(b)).astype(float)
    return _pearson(ar, br)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def scalar_axis_agreement(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Agreement between two raters on one ordinal (1–7) axis across segments."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    diff = np.abs(a - b)
    try:
        kappa = float(cohen_kappa_score(a.astype(int), b.astype(int), weights="quadratic"))
    except Exception:  # noqa: BLE001 — degenerate (single class) → undefined
        kappa = float("nan")
    return {
        "spearman": _spearman(a, b),
        "pearson": _pearson(a, b),
        "weighted_kappa": kappa,
        "mean_abs_diff": float(np.mean(diff)),
        "within1_rate": float(np.mean(diff <= 1)),
    }


def forced_choice_agreement(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Agreement on one nominal forced-choice axis (values are 1-based option indices)."""
    a = np.asarray(a, dtype=int)
    b = np.asarray(b, dtype=int)
    try:
        kappa = float(cohen_kappa_score(a, b))
    except Exception:  # noqa: BLE001
        kappa = float("nan")
    return {"exact_match_rate": float(np.mean(a == b)), "cohen_kappa": kappa}


def correlation_matrix(m: np.ndarray) -> np.ndarray:
    """Pearson correlation across columns (axes) of a segments×axes matrix."""
    return np.corrcoef(m, rowvar=False)


def redundant_pairs(corr: np.ndarray, ids: list[str], threshold: float = 0.8) -> list[tuple]:
    out: list[tuple[str, str, float]] = []
    n = len(ids)
    for i in range(n):
        for j in range(i + 1, n):
            r = corr[i, j]
            if np.isfinite(r) and abs(r) >= threshold:
                out.append((ids[i], ids[j], float(r)))
    return sorted(out, key=lambda t: -abs(t[2]))


def run_pca(m: np.ndarray, ids: list[str]) -> dict:
    """PCA over a segments×axes matrix (standardized). Returns explained variance and the
    top-loading axes per component — the emergent latent-factor structure."""
    x = StandardScaler().fit_transform(m)
    pca = PCA().fit(x)
    evr = pca.explained_variance_ratio_
    cum = np.cumsum(evr)
    loadings = pca.components_  # (n_components, n_axes)
    top_axes = []
    for comp in loadings[: min(6, len(loadings))]:
        order = np.argsort(-np.abs(comp))[:5]
        top_axes.append([(ids[k], round(float(comp[k]), 2)) for k in order])
    return {
        "explained_variance_ratio": [round(float(v), 4) for v in evr],
        "cumulative": [round(float(v), 4) for v in cum],
        "n_for_80pct": int(np.searchsorted(cum, 0.80) + 1),
        "n_for_90pct": int(np.searchsorted(cum, 0.90) + 1),
        "top_axes_per_component": top_axes,
    }


def twin_consistency(m: np.ndarray, seg_ids: list[str], pairs: dict[str, str]) -> dict:
    """Mean |Δ| between twin segments (same target profile) vs. the all-pairs baseline.
    `pairs` maps segment_id → pair_group; a group with 2 members is a twin pair."""
    idx = {sid: i for i, sid in enumerate(seg_ids)}
    groups: dict[str, list[str]] = {}
    for sid, g in pairs.items():
        if g:
            groups.setdefault(g, []).append(sid)
    twin_dists = []
    for members in groups.values():
        if len(members) == 2 and all(x in idx for x in members):
            twin_dists.append(float(np.mean(np.abs(m[idx[members[0]]] - m[idx[members[1]]]))))
    n = len(seg_ids)
    all_dists = [
        float(np.mean(np.abs(m[i] - m[j]))) for i in range(n) for j in range(i + 1, n)
    ]
    return {
        "n_twin_pairs": len(twin_dists),
        "mean_twin_distance": round(float(np.mean(twin_dists)), 3) if twin_dists else None,
        "mean_all_pairs_distance": round(float(np.mean(all_dists)), 3) if all_dists else None,
        "twin_distances": [round(d, 3) for d in twin_dists],
    }


# ---- storage-backed loading --------------------------------------------------------


def load_rater_matrices(
    axes: list[AxisDef], *, source: str = "pilot", axes_version: int | None = None
) -> tuple[list[str], dict[str, np.ndarray], dict[str, np.ndarray], dict[str, dict]]:
    """Load value + confidence matrices per rater over the pilot segments.

    Returns (segment_ids, values_by_rater, confidence_by_rater, meta_by_segment), where
    each matrix is segments×axes aligned to `segment_ids` and the axis order. Only segments
    whose frontmatter `source` matches (the pilot marker) are included. Selection is
    **newest-wins** per (rater, segment) — first-wins would silently ignore every
    re-rating — within ONE `axes_version` cohort (default: the registry's current
    version); re-anchored cohorts are never pooled. Segments unrated under that version
    stay NaN."""
    if axes_version is None:
        axes_version = load_axes_version()
    axis_ids = [a.id for a in axes]
    segs = [s for s in storage.list_segments() if s.get("source") == source]
    seg_ids = sorted(s["id"] for s in segs)
    meta: dict[str, dict] = {}
    vals: dict[str, dict[str, dict[str, int]]] = {}
    confs: dict[str, dict[str, dict[str, int]]] = {}
    for sid in seg_ids:
        seg = storage.load_segment(sid) or {}
        meta[sid] = {"profile": seg.get("profile"), "pair": seg.get("pair")}
        for rid, r in storage.latest_ratings(sid, axes_version=axes_version).items():
            vals.setdefault(rid, {})[sid] = {sc.axis_id: sc.value for sc in r.scores}
            confs.setdefault(rid, {})[sid] = {sc.axis_id: sc.confidence for sc in r.scores}

    def _matrix(store: dict[str, dict[str, dict[str, int]]], rater: str) -> np.ndarray:
        m = np.full((len(seg_ids), len(axis_ids)), np.nan)
        for i, sid in enumerate(seg_ids):
            row = store.get(rater, {}).get(sid, {})
            for j, aid in enumerate(axis_ids):
                if aid in row:
                    m[i, j] = row[aid]
        return m

    raters = sorted(vals)
    values_by_rater = {r: _matrix(vals, r) for r in raters}
    confidence_by_rater = {r: _matrix(confs, r) for r in raters}
    return seg_ids, values_by_rater, confidence_by_rater, meta


# ---- report ------------------------------------------------------------------------


def build_report(
    axes: list[AxisDef], *, source: str = "pilot", axes_version: int | None = None
) -> dict:
    if axes_version is None:
        axes_version = load_axes_version()
    seg_ids, values, confidence, meta = load_rater_matrices(
        axes, source=source, axes_version=axes_version
    )
    raters = sorted(values)
    axis_ids = [a.id for a in axes]
    kind = {a.id: a.kind for a in axes}
    names = {a.id: a.name for a in axes}
    scalar_ids = [a.id for a in axes if a.kind == "scalar"]

    report: dict = {
        "n_segments": len(seg_ids),
        "axes_version": axes_version,
        "raters": raters,
        "segment_ids": seg_ids,
    }
    if len(raters) < 2 or len(seg_ids) < 2:
        report["error"] = "need >=2 raters and >=2 segments"
        return report

    col = {aid: j for j, aid in enumerate(axis_ids)}
    pairs = [
        (raters[i], raters[j])
        for i in range(len(raters))
        for j in range(i + 1, len(raters))
    ]
    report["rater_pairs"] = [f"{r1} vs {r2}" for r1, r2 in pairs]

    def _pairwise(aid: str, r1: str, r2: str) -> dict | None:
        """Agreement over the segments BOTH raters scored (pairwise-complete), so a rater
        who covered only part of the corpus — a human scoring 8 of n — still counts."""
        j = col[aid]
        a, b = values[r1][:, j], values[r2][:, j]
        both = ~np.isnan(a) & ~np.isnan(b)
        if int(both.sum()) < 2:
            return None
        fn = forced_choice_agreement if kind[aid] == "forced_choice" else scalar_axis_agreement
        m = fn(a[both], b[both])
        m["n"] = int(both.sum())
        return m

    # per-axis agreement, one entry per rater pair + a headline mean across pairs
    agree: dict[str, dict] = {}
    for aid in axis_ids:
        per_pair: dict[str, dict] = {}
        for r1, r2 in pairs:
            m = _pairwise(aid, r1, r2)
            if m is not None:
                per_pair[f"{r1} vs {r2}"] = m
        conf_all = np.concatenate([confidence[r][:, col[aid]] for r in raters])
        conf_ok = conf_all[~np.isnan(conf_all)]
        entry: dict = {
            "name": names[aid],
            "kind": kind[aid],
            "mean_confidence": round(float(conf_ok.mean()), 2) if conf_ok.size else float("nan"),
            "pairs": per_pair,
        }
        # Headline metrics = mean across pairs, so the verdict and the printed report stay
        # one-dimensional while the per-pair detail is preserved underneath.
        metric_keys = {k for m in per_pair.values() for k in m if k != "n"}
        for key in metric_keys:
            vals_ = [
                m[key] for m in per_pair.values()
                if key in m and np.isfinite(m[key])
            ]
            if vals_:
                entry[key] = round(float(np.mean(vals_)), 4)
        agree[aid] = entry
    report["axis_agreement"] = agree

    # consensus over scalar axes (mean across ALL raters) → correlation + PCA
    scal_cols = [col[a] for a in scalar_ids]
    stack = np.stack([values[r][:, scal_cols] for r in raters])  # (raters, segments, axes)
    # Keep only segments where every scalar axis has at least one rater; ragged coverage
    # would otherwise produce all-NaN means.
    complete = (~np.isnan(stack).all(axis=0)).all(axis=1)
    n_complete = int(complete.sum())
    report["n_segments_in_pca"] = n_complete
    if n_complete >= 2:
        consensus = np.nanmean(stack[:, complete, :], axis=0)
        kept = [s for s, k in zip(seg_ids, complete, strict=True) if k]
        corr = correlation_matrix(consensus)
        report["redundant_pairs"] = redundant_pairs(corr, scalar_ids, threshold=0.8)
        report["pca"] = run_pca(consensus, scalar_ids)
        report["twin_consistency"] = twin_consistency(
            consensus, kept, {sid: meta[sid].get("pair") for sid in kept}
        )
    else:
        report["redundant_pairs"] = []
        report["pca"] = None
        report["twin_consistency"] = None

    # verdicts
    reliable, ambiguous = [], []
    for aid, m in agree.items():
        primary = m.get("within1_rate", m.get("exact_match_rate", 0.0))
        if primary >= 0.7 and m["mean_confidence"] >= 3.0:
            reliable.append(aid)
        if primary < 0.5 or m["mean_confidence"] < 2.5:
            ambiguous.append(aid)
    report["verdict"] = {
        "reliable_axes": reliable,
        "ambiguous_axes": ambiguous,
        "redundant_axis_pairs": [(x, y) for x, y, _ in report["redundant_pairs"]],
    }
    return report


def format_report(report: dict) -> str:
    if report.get("error"):
        return f"Reliability: {report['error']} (segments={report.get('n_segments')})."
    lines = [
        "# LSAP-1 — reliability report",
        "",
        f"segments: {report['n_segments']}   raters: {', '.join(report['raters'])}"
        f"   axes_version: {report.get('axes_version', 1)}",
        f"rater pairs: {', '.join(report.get('rater_pairs', [])) or '—'}"
        f"   segments in PCA: {report.get('n_segments_in_pca', '—')}",
        "",
        "## Per-axis agreement, averaged across rater pairs"
        " (scalar: within-1 rate; forced-choice: exact-match)",
    ]
    nan = float("nan")
    multi = len(report.get("rater_pairs", [])) > 1
    for aid, m in report["axis_agreement"].items():
        if m["kind"] == "forced_choice":
            lines.append(
                f"  {aid:3} {m['name']:26} exact={m.get('exact_match_rate', nan):.2f} "
                f"kappa={m.get('cohen_kappa', nan):+.2f} conf={m['mean_confidence']}"
            )
        else:
            lines.append(
                f"  {aid:3} {m['name']:26} within1={m.get('within1_rate', nan):.2f} "
                f"spearman={m.get('spearman', nan):+.2f} "
                f"wkappa={m.get('weighted_kappa', nan):+.2f} "
                f"|d|={m.get('mean_abs_diff', nan):.2f} conf={m['mean_confidence']}"
            )
        if multi:  # show each pair once there is more than one (e.g. a human rater)
            for label, pm in m.get("pairs", {}).items():
                primary = pm.get("within1_rate", pm.get("exact_match_rate", nan))
                lines.append(f"        {label}: {primary:.2f} (n={pm['n']})")
    v = report["verdict"]
    lines += [
        "",
        f"## Reliable axes ({len(v['reliable_axes'])}): {', '.join(v['reliable_axes']) or '—'}",
        f"## Ambiguous axes ({len(v['ambiguous_axes'])}): {', '.join(v['ambiguous_axes']) or '—'}",
        "",
        "## Redundant axis pairs (|r| >= 0.8)",
    ]
    lines += [f"  {x} ~ {y}  r={r:+.2f}" for x, y, r in report["redundant_pairs"]] or ["  none"]
    p = report["pca"]
    if p is not None:
        lines += [
            "",
            "## PCA over scalar axes",
            f"  explained variance (top): {p['explained_variance_ratio'][:8]}",
            f"  cumulative (top): {p['cumulative'][:8]}",
            f"  components for 80% / 90%: {p['n_for_80pct']} / {p['n_for_90pct']}",
            "  top-loading axes per component:",
        ]
        for i, comp in enumerate(p["top_axes_per_component"], 1):
            lines.append(f"    PC{i}: " + ", ".join(f"{a}({w:+.2f})" for a, w in comp))
    t = report["twin_consistency"]
    if t is not None:
        lines += [
            "",
            "## Twin-pair consistency (mean |d| over scalar axes)",
            f"  twin pairs: {t['n_twin_pairs']}   twin mean: {t['mean_twin_distance']}   "
            f"all-pairs mean: {t['mean_all_pairs_distance']}",
        ]
    return "\n".join(lines)


# ---- before/after (anchor revisions) ------------------------------------------------


def available_versions(*, source: str = "pilot") -> list[int]:
    """Distinct `axes_version` cohorts present across the source segments' ratings."""
    versions: set[int] = set()
    for s in storage.list_segments():
        if s.get("source") != source:
            continue
        for r in storage.load_ratings(s["id"]):
            versions.add(r.axes_version)
    return sorted(versions)


def compare_reports(before: dict, after: dict) -> dict:
    """Per-axis primary agreement (within-1 / exact-match) side by side across two
    axes_version cohorts. A drop > 0.10 on any axis is flagged — the M5 gate."""
    axes_cmp: dict[str, dict] = {}
    regressions: list[str] = []
    for aid, m_new in after.get("axis_agreement", {}).items():
        m_old = before.get("axis_agreement", {}).get(aid, {})
        key = "exact_match_rate" if m_new["kind"] == "forced_choice" else "within1_rate"
        old, new = m_old.get(key), m_new.get(key)
        delta = round(new - old, 4) if old is not None and new is not None else None
        axes_cmp[aid] = {
            "name": m_new["name"],
            "kind": m_new["kind"],
            "before": old,
            "after": new,
            "delta": delta,
        }
        if delta is not None and delta < -0.10:
            regressions.append(aid)
    return {
        "before_axes_version": before.get("axes_version"),
        "after_axes_version": after.get("axes_version"),
        "axes": axes_cmp,
        "regressions": regressions,
    }


def format_comparison(cmp: dict) -> str:
    v_old, v_new = cmp["before_axes_version"], cmp["after_axes_version"]
    lines = [
        "",
        f"## Before/after re-anchoring — axes_version {v_old} vs {v_new}",
        "   (per-axis primary agreement: within-1 for scalar, exact-match for forced-choice)",
        f"   {'axis':30}  v{v_old}     v{v_new}     delta",
    ]
    for aid, c in cmp["axes"].items():
        old = "  —  " if c["before"] is None else f"{c['before']:.2f}"
        new = "  —  " if c["after"] is None else f"{c['after']:.2f}"
        delta = "  —  " if c["delta"] is None else f"{c['delta']:+.2f}"
        mark = "  <-- re-anchored" if aid in ("L1", "L3") else ""
        lines.append(f"   {aid:3} {c['name']:26}  {old}   {new}   {delta}{mark}")
    reg = ", ".join(cmp["regressions"]) or "none"
    lines.append(f"   regressions (> 0.10 drop): {reg}")
    return "\n".join(lines)


def main() -> None:
    try:  # Windows consoles default to cp1252; the report is UTF-8.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    axes = load_axes()
    current = load_axes_version()
    report = build_report(axes, axes_version=current)
    text = format_report(report)
    # When an older anchor cohort exists, show before/after side by side, each column
    # labelled with the axes_version it came from (the M5 acceptance view).
    prior = [v for v in available_versions() if v < current]
    if prior and not report.get("error"):
        before = build_report(axes, axes_version=prior[-1])
        if not before.get("error"):
            report["before_after"] = compare_reports(before, report)
            text += "\n" + format_comparison(report["before_after"])
    out_dir = storage.data_dir() / "reliability"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(text + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(text)
    print(f"\nwrote {out_dir / 'report.md'} and metrics.json")


if __name__ == "__main__":
    main()
