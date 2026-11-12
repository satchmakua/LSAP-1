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
from lsap.coordinates.projection import PANEL_MIN_COVERAGE, consensus_panel
from lsap.instrument.schema import AxisDef, load_axes, load_axes_version

# ---- pure metrics (unit-tested offline) --------------------------------------------


def _average_ranks(x: np.ndarray) -> np.ndarray:
    """1-based ranks with tied values sharing their average rank — the standard Spearman
    convention. Ordinal 1–7 scores are almost all ties, so the tie rule is not a detail:
    breaking ties by position (argsort of argsort) moved rho by up to 0.17 on real data."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1)
    _, inverse, counts = np.unique(x, return_inverse=True, return_counts=True)
    return np.bincount(inverse, weights=ranks)[inverse] / counts[inverse]


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rho = Pearson on average ranks. Returns 0.0 when either side is constant."""
    return _pearson(_average_ranks(a), _average_ranks(b))


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


def _match_components(a: np.ndarray, b: np.ndarray) -> list[float]:
    """Greedily match rows of `b` (components × axes) to rows of `a` by |Pearson r| over
    the axis loadings, each row used once. A PCA component's sign and order are
    arbitrary, so matching is by absolute correlation. Returns |r| per row of `a`."""
    taken: set[int] = set()
    out: list[float] = []
    for i in range(a.shape[0]):
        best_j, best_r = -1, 0.0
        for j in range(b.shape[0]):
            if j in taken:
                continue
            r = abs(_pearson(a[i], b[j]))
            if r >= best_r:
                best_j, best_r = j, r
        taken.add(best_j)
        out.append(best_r)
    return out


def split_half_stability(
    m: np.ndarray, *, n_components: int = 5, n_splits: int = 20, seed: int = 0
) -> dict:
    """Fit PCA on two random halves of the segments and correlate the loadings (M6).

    Averaged over `n_splits` random splits (seeded — no wall-clock randomness). High
    mean |r| on the top components means the factor structure is not an artifact of
    which half of the corpus you look at; low means the fit is not yet stable at this n.
    """
    x = np.asarray(m, dtype=float)
    n = x.shape[0]
    half = n // 2
    k = int(min(n_components, half - 1, x.shape[1]))
    if half < 4 or k < 1:
        return {"error": f"too few segments for a split-half check (n={n})"}
    rng = np.random.default_rng(seed)
    per_comp = np.zeros(k)
    for _ in range(n_splits):
        idx = rng.permutation(n)
        halves = []
        for part in (idx[:half], idx[half : 2 * half]):
            xs = StandardScaler().fit_transform(x[part])
            halves.append(PCA(n_components=k).fit(xs).components_)
        per_comp += np.array(_match_components(halves[0], halves[1]))
    per_comp /= n_splits
    return {
        "n_splits": n_splits,
        "n_half": half,
        "n_components": k,
        "mean_abs_r_per_component": [round(float(v), 3) for v in per_comp],
        "mean_abs_r": round(float(per_comp.mean()), 3),
    }


def origin_generalization(
    m: np.ndarray,
    origins: list[str],
    axis_ids: list[str],
    *,
    n_components: int = 5,
    n_splits: int = 200,
    seed: int = 0,
) -> dict | None:
    """Do factors fitted on the majority origin describe the minority as well as they
    describe held-out majority segments (M6)?

    An out-of-sample test, because the in-sample one cannot fail: loadings fitted on the
    majority alone always resemble loadings fitted on majority + a small minority, since
    most of the rows are shared. Here each seeded split holds out as many majority
    segments as there are minority ones, fits scaler + PCA on the rest, and measures the
    share of variance the factors capture in (a) the held-out majority and (b) the
    minority, under the identical fit. A gap means the minority carries variance the
    factors do not describe — the structure is partly a property of the majority origin.

    Extremity confounds the raw gap (segments near the centroid are proportionally
    noisier and captured less), so a second gap restricts the held-out majority to the
    minority's own extremity range. Small minority n: indicative, not conclusive.
    """
    counts = {o: origins.count(o) for o in set(origins)}
    if len(counts) < 2:
        return None
    major = max(counts, key=lambda o: counts[o])
    x = np.asarray(m, dtype=float)
    is_major = np.array([o == major for o in origins])
    maj, mnr = x[is_major], x[~is_major]
    n_min = len(mnr)
    k = int(min(n_components, len(maj) - n_min - 1, x.shape[1]))
    if n_min < 5 or len(maj) - n_min < 10 or k < 1:
        return None

    rng = np.random.default_rng(seed)
    hold_cap, min_cap = [], []  # pooled capture per split
    hold_norm, hold_seg, min_norm, min_seg = [], [], [], []  # per-segment, for matching
    for _ in range(n_splits):
        idx = rng.permutation(len(maj))
        hold, train = idx[:n_min], idx[n_min:]
        scaler = StandardScaler().fit(maj[train])
        comps = PCA(n_components=k).fit(scaler.transform(maj[train])).components_
        for rows, caps, norms, segs in (
            (maj[hold], hold_cap, hold_norm, hold_seg),
            (mnr, min_cap, min_norm, min_seg),
        ):
            z = scaler.transform(rows)
            total = (z**2).sum(axis=1)
            kept = ((z @ comps.T) ** 2).sum(axis=1)
            caps.append(float(kept.sum() / total.sum()))
            norms.extend(total)
            segs.extend(kept / np.where(total == 0, 1.0, total))
    hold_cap_a, min_cap_a = np.array(hold_cap), np.array(min_cap)
    hold_norm_a, hold_seg_a = np.array(hold_norm), np.array(hold_seg)
    min_norm_a, min_seg_a = np.array(min_norm), np.array(min_seg)
    in_range = (hold_norm_a >= min_norm_a.min()) & (hold_norm_a <= min_norm_a.max())
    matched_gap = (
        float(hold_seg_a[in_range].mean() - min_seg_a.mean()) if in_range.any() else None
    )

    offsets = mnr.mean(axis=0) - maj.mean(axis=0)
    order = np.argsort(-np.abs(offsets))[:5]

    def _summary(a: np.ndarray) -> dict:
        lo, hi = np.percentile(a, [5, 95])
        return {"mean": round(float(a.mean()), 3), "p05": round(float(lo), 3),
                "p95": round(float(hi), 3)}

    return {
        "majority_origin": major,
        "n_majority": int(len(maj)),
        "n_minority": int(n_min),
        "n_components": k,
        "n_splits": n_splits,
        "captured_holdout_majority": _summary(hold_cap_a),
        "captured_minority": _summary(min_cap_a),
        "gap": round(float((hold_cap_a - min_cap_a).mean()), 3),
        "gap_matched_on_extremity": None if matched_gap is None else round(matched_gap, 3),
        "minority_lower_in_share_of_splits": round(float((min_cap_a < hold_cap_a).mean()), 3),
        "top_axis_offsets": [[axis_ids[i], round(float(offsets[i]), 2)] for i in order],
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
    axes: list[AxisDef],
    *,
    source: str = "pilot",
    axes_version: int | None = None,
    only_segments: set[str] | None = None,
) -> tuple[list[str], dict[str, np.ndarray], dict[str, np.ndarray], dict[str, dict]]:
    """Load value + confidence matrices per rater over the pilot segments.

    Returns (segment_ids, values_by_rater, confidence_by_rater, meta_by_segment), where
    each matrix is segments×axes aligned to `segment_ids` and the axis order. Only segments
    whose frontmatter `source` matches (the pilot marker) are included. Selection is
    **newest-wins** per (rater, segment) — first-wins would silently ignore every
    re-rating — within ONE `axes_version` cohort (default: the registry's current
    version); re-anchored cohorts are never pooled. Segments unrated under that version
    stay NaN. `only_segments` restricts to a given set — used to compare two anchor
    cohorts over the segments they share, so corpus growth can't masquerade as an
    anchor effect."""
    if axes_version is None:
        axes_version = load_axes_version()
    axis_ids = [a.id for a in axes]
    segs = [s for s in storage.list_segments() if s.get("source") == source]
    seg_ids = sorted(
        s["id"] for s in segs if only_segments is None or s["id"] in only_segments
    )
    meta: dict[str, dict] = {}
    vals: dict[str, dict[str, dict[str, int]]] = {}
    confs: dict[str, dict[str, dict[str, int]]] = {}
    for sid in seg_ids:
        seg = storage.load_segment(sid) or {}
        meta[sid] = {
            "profile": seg.get("profile"),
            "pair": seg.get("pair"),
            "origin": seg.get("origin"),  # None/"model" vs "public-domain" (M6)
        }
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
    axes: list[AxisDef],
    *,
    source: str = "pilot",
    axes_version: int | None = None,
    only_segments: set[str] | None = None,
    only_raters: set[str] | None = None,
) -> dict:
    if axes_version is None:
        axes_version = load_axes_version()
    seg_ids, values, confidence, meta = load_rater_matrices(
        axes, source=source, axes_version=axes_version, only_segments=only_segments
    )
    if only_raters is not None:  # compare cohorts over the raters they share
        values = {r: m for r, m in values.items() if r in only_raters}
        confidence = {r: m for r, m in confidence.items() if r in only_raters}
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

    # per-axis agreement, one entry per rater pair + an n-weighted headline across pairs
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
        # Headline metrics = mean across pairs weighted by each pair's n, so the verdict
        # and the printed report stay one-dimensional while the per-pair detail is kept
        # underneath. Weighting matters once coverage is ragged: a pair that shares 8
        # segments must not count as much as one that shares 100.
        metric_keys = {k for m in per_pair.values() for k in m if k != "n"}
        for key in metric_keys:
            pts = [
                (m[key], m["n"]) for m in per_pair.values()
                if key in m and np.isfinite(m[key])
            ]
            if pts:
                vals_, weights = zip(*pts, strict=True)
                entry[key] = round(float(np.average(vals_, weights=weights)), 4)
        agree[aid] = entry
    report["axis_agreement"] = agree

    # consensus over scalar axes (mean across the PANEL) → correlation + PCA
    scal_cols = [col[a] for a in scalar_ids]
    coverage = {
        r: float((~np.isnan(values[r][:, scal_cols]).all(axis=1)).mean()) for r in raters
    }
    panel = consensus_panel(coverage)
    report["consensus_raters"] = panel
    stack = np.stack([values[r][:, scal_cols] for r in panel])  # (raters, segments, axes)
    # Keep only segments where every scalar axis has at least one panel rater; ragged
    # coverage would otherwise produce all-NaN means.
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
        report["split_half"] = (
            split_half_stability(consensus) if n_complete >= 10 else None
        )
        origins = [(meta[s].get("origin") or "model") for s in kept]
        report["origin_generalization"] = origin_generalization(
            consensus, origins, scalar_ids
        )
    else:
        report["redundant_pairs"] = []
        report["pca"] = None
        report["twin_consistency"] = None
        report["split_half"] = None
        report["origin_generalization"] = None

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

    # human↔model divergence (M7): the axes where a human rater and a model disagree most.
    # This is DATA under Charter P2 — reported, never "corrected".
    report["human_model_divergence"] = human_model_divergence(agree, raters)
    return report


def human_model_divergence(agree: dict, raters: list[str]) -> dict | None:
    """Per human-vs-model rater pair, the axes ranked by disagreement (1 − primary
    agreement over the segments both rated). None when no human rater is present.
    Charter P2: divergence is data, not error — this names it, it does not fix it."""
    humans = [r for r in raters if r.startswith("human:")]
    models = [r for r in raters if not r.startswith("human:")]
    if not humans or not models:
        return None
    out: dict[str, list] = {}
    for h in humans:
        for mdl in models:
            key = f"{h} vs {mdl}"
            rev = f"{mdl} vs {h}"
            rows = []
            for aid, m in agree.items():
                pm = m.get("pairs", {}).get(key) or m.get("pairs", {}).get(rev)
                if pm is None:
                    continue
                primary = pm.get("within1_rate", pm.get("exact_match_rate"))
                if primary is None:
                    continue
                rows.append(
                    {"axis_id": aid, "name": m["name"], "kind": m["kind"],
                     "agreement": round(float(primary), 3), "n": pm["n"]}
                )
            if rows:
                out[key] = sorted(rows, key=lambda r: r["agreement"])
    return out or None


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
        f"consensus panel (raters covering >= {PANEL_MIN_COVERAGE:.0%} of segments): "
        f"{', '.join(report.get('consensus_raters', [])) or '—'}",
        "",
        "## Per-axis agreement, n-weighted across rater pairs"
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
    hmd = report.get("human_model_divergence")
    if hmd:
        lines.append("")
        lines.append(
            "## Human↔model divergence — where a human and a model most disagree"
        )
        lines.append(
            "   (Charter P2: this is DATA, not error — reported, never corrected)"
        )
        for pair_label, rows in hmd.items():
            lines.append(f"  {pair_label}:")
            for r in rows[:5]:  # the five widest gaps
                lines.append(
                    f"      {r['axis_id']:3} {r['name']:26} "
                    f"agreement={r['agreement']:.2f} (n={r['n']})"
                )
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
    sh = report.get("split_half")
    if sh and not sh.get("error"):
        lines += [
            "",
            "## Split-half stability (PCA loadings, "
            f"{sh['n_splits']} seeded splits of {sh['n_half']}+{sh['n_half']})",
            f"  |r| per component: {sh['mean_abs_r_per_component']}   "
            f"mean: {sh['mean_abs_r']}",
        ]
    og = report.get("origin_generalization")
    if og is not None:
        hm, mn = og["captured_holdout_majority"], og["captured_minority"]
        matched = og["gap_matched_on_extremity"]
        lines += [
            "",
            f"## Origin check — do factors fitted on {og['majority_origin']}-written "
            "segments describe the others?",
            f"   ({og['majority_origin']} n={og['n_majority']} vs other origins "
            f"n={og['n_minority']}; out-of-sample, {og['n_splits']} seeded splits; "
            "indicative only at this n)",
            f"  variance captured by {og['n_components']} factors — "
            f"held-out {og['majority_origin']}: {hm['mean']:.3f} "
            f"({hm['p05']:.3f}–{hm['p95']:.3f})   "
            f"other origins: {mn['mean']:.3f} ({mn['p05']:.3f}–{mn['p95']:.3f})",
            f"  gap: {og['gap']:+.3f}   matched on extremity: "
            + ("—" if matched is None else f"{matched:+.3f}")
            + f"   other origins lower in {og['minority_lower_in_share_of_splits']:.0%}"
            " of splits",
            "  largest per-axis consensus offsets (minority − majority): "
            + ", ".join(f"{a}({v:+.2f})" for a, v in og["top_axis_offsets"]),
        ]
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


def segments_rated_under(version: int, *, source: str = "pilot") -> set[str]:
    """Segments with at least 2 raters under `version` — the comparable set."""
    out: set[str] = set()
    for s in storage.list_segments():
        if s.get("source") != source:
            continue
        if len(storage.latest_ratings(s["id"], axes_version=version)) >= 2:
            out.add(s["id"])
    return out


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
        "n_segments": after.get("n_segments"),
        "axes": axes_cmp,
        "regressions": regressions,
    }


def format_comparison(cmp: dict) -> str:
    v_old, v_new = cmp["before_axes_version"], cmp["after_axes_version"]
    lines = [
        "",
        f"## Before/after re-anchoring — axes_version {v_old} vs {v_new}",
        f"   Like-for-like: the {cmp.get('n_segments')} segments rated under BOTH cohorts,",
        "   so corpus growth cannot masquerade as an anchor effect.",
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
    # labelled with the axes_version it came from (the M5 acceptance view). "Before" is
    # the OLDEST cohort — the pre-re-anchor baseline, not an intermediate revision.
    prior = [v for v in available_versions() if v < current]
    if prior and not report.get("error"):
        # Compare over the segments rated under BOTH cohorts only. Once the corpus grows,
        # an unrestricted comparison would mix an anchor change with a composition change.
        common = segments_rated_under(prior[0]) & segments_rated_under(current)
        if len(common) >= 2:
            before = build_report(axes, axes_version=prior[0], only_segments=common)
            after_same = build_report(axes, axes_version=current, only_segments=common)
            # ...and over the raters both cohorts share: a rater added since (a human)
            # would otherwise change the headline for reasons unrelated to the anchors.
            shared = set(before.get("raters", [])) & set(after_same.get("raters", []))
            if shared != set(before.get("raters", [])) | set(after_same.get("raters", [])):
                before = build_report(
                    axes, axes_version=prior[0], only_segments=common, only_raters=shared
                )
                after_same = build_report(
                    axes, axes_version=current, only_segments=common, only_raters=shared
                )
            if not before.get("error") and not after_same.get("error"):
                report["before_after"] = compare_reports(before, after_same)
                text += "\n" + format_comparison(report["before_after"])
    out_dir = storage.data_dir() / "reliability"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(text + "\n", encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(text)
    print(f"\nwrote {out_dir / 'report.md'} and metrics.json")


if __name__ == "__main__":
    main()
