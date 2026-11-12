"""L2/L3 — the fitted projection from the anchored axes into C-space (DESIGN.md §4.2).

Fitted over the rated pilot corpus and persisted to `coordinates/model.json` so the map
and every later projection are reproducible. Pipeline: consensus across raters →
standardize the scalar axes → PCA → the first five components are the locked factors;
**C6 is the acknowledged residual** (the share of variance the five do not capture —
Charter P5, never let the model silently claim completeness).

Factor labels are **derived from each component's own top loadings**, not assumed: M2
showed the hypothesised Big-Five names do not map 1:1 onto the data (the Consciousness
axes collapse into a single interiority factor). Naming a component after what it
actually loads on keeps the label honest (Charter P1/P6).

Label space. MAY read `instrument` + `storage`; never the reverse (the firewall).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from lsap import storage
from lsap.instrument.schema import AxisDef, load_axes, load_axes_version

N_FACTORS = 5


class CVector(BaseModel):
    """A text's position in C-space: the locked factors, each normalized to [0,1] over
    the fitted corpus, plus the acknowledged residual (Charter P5)."""

    coords: list[float]
    residual: float


class Neighbor(BaseModel):
    segment_id: str
    distance: float
    profile: str | None = None


def default_model_path() -> Path:
    return storage.data_dir() / "coordinates" / "model.json"


# ---- consensus helpers --------------------------------------------------------------


#: A rater joins the consensus panel only if it covers at least this share of the
#: segments. A rater who has scored 8 of 100 is compared against the panel, never pooled
#: into it — otherwise a segment's consensus would depend on who happened to rate it.
PANEL_MIN_COVERAGE = 0.9


def consensus_panel(coverage: dict[str, float]) -> list[str]:
    """The raters whose ratings are averaged into the consensus: those covering at least
    `PANEL_MIN_COVERAGE` of the segments. Falls back to every rater when none qualifies
    (e.g. midway through a re-rate), which is the pre-panel behaviour."""
    panel = sorted(r for r, share in coverage.items() if share >= PANEL_MIN_COVERAGE)
    return panel or sorted(coverage)


def consensus_for_segment(
    segment_id: str,
    axis_ids: list[str],
    *,
    axes_version: int | None = None,
    raters: list[str] | None = None,
) -> dict[str, float] | None:
    """Mean value per axis across raters — **newest** rating per rater, within one
    `axes_version` cohort (None = the segment's newest; cohorts are never pooled).
    `raters` restricts the mean to a consensus panel: when any panel member rated the
    segment, raters outside the panel are ignored; a segment no panel member has rated
    falls back to whoever did rate it. None if unrated under that version."""
    latest = storage.latest_ratings(segment_id, axes_version=axes_version)
    if not latest:
        return None
    if raters:
        on_panel = {rid: r for rid, r in latest.items() if rid in raters}
        latest = on_panel or latest
    seen = {rid: {s.axis_id: s.value for s in r.scores} for rid, r in latest.items()}
    out: dict[str, float] = {}
    for a in axis_ids:
        vals = [d[a] for d in seen.values() if a in d]
        if not vals:
            return None
        out[a] = float(np.mean(vals))
    return out


# ---- the model ----------------------------------------------------------------------


class ProjectionModel:
    """Wraps the fitted, serializable projection."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.d = data

    # --- fit ---
    @classmethod
    def fit(
        cls,
        matrix: np.ndarray,
        axis_ids: list[str],
        axis_names: dict[str, str],
        segments: list[dict],
    ) -> ProjectionModel:
        """`matrix` is (n_segments, n_axes) consensus values aligned to `axis_ids`;
        `segments` carries id/profile/pair per row."""
        x = np.asarray(matrix, dtype=float)
        if x.shape[0] < 2:
            raise ValueError("need at least 2 rated segments to fit a projection")
        scaler = StandardScaler().fit(x)
        xs = scaler.transform(x)
        n_comp = int(min(N_FACTORS, xs.shape[0] - 1, xs.shape[1]))
        pca = PCA(n_components=n_comp).fit(xs)
        # Drop degenerate directions: a ~0-variance component carries no information, and
        # min-max normalizing it amplifies floating-point noise across the whole [0,1] range.
        keep = [i for i in range(n_comp) if pca.explained_variance_ratio_[i] > 1e-8]
        comps = pca.components_[keep]
        evr = pca.explained_variance_ratio_[keep]
        # Same linear map as `project()`, so fitted points and later projections agree exactly.
        scores = xs @ comps.T
        lo, hi = scores.min(axis=0), scores.max(axis=0)

        factors = []
        for i, comp in enumerate(comps):
            order = np.argsort(-np.abs(comp))[:3]
            tops = [[axis_ids[k], round(float(comp[k]), 3)] for k in order]
            factors.append(
                {
                    "id": f"C{i + 1}",
                    "label": " · ".join(axis_names.get(a, a) for a, _ in tops),
                    "explained_variance": round(float(evr[i]), 4),
                    "top_axes": tops,
                }
            )

        def _norm(row: np.ndarray) -> list[float]:
            span = np.where(hi - lo == 0, 1.0, hi - lo)
            return [round(float(v), 4) for v in np.clip((row - lo) / span, 0.0, 1.0)]

        points = [
            {
                "segment_id": seg["id"],
                "profile": seg.get("profile"),
                "pair": seg.get("pair"),
                "coords": _norm(scores[i]),
                "scores": [round(float(v), 6) for v in scores[i]],
            }
            for i, seg in enumerate(segments)
        ]

        return cls(
            {
                "version": 1,
                "axis_ids": list(axis_ids),
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
                "components": comps.tolist(),
                "explained_variance_ratio": [round(float(v), 4) for v in evr],
                "residual": round(float(1.0 - float(np.sum(evr))), 4),
                "score_min": lo.tolist(),
                "score_max": hi.tolist(),
                "factors": factors,
                "points": points,
                "n_segments": int(x.shape[0]),
            }
        )

    # --- use ---
    @property
    def axis_ids(self) -> list[str]:
        return self.d["axis_ids"]

    @property
    def factors(self) -> list[dict]:
        return self.d["factors"]

    @property
    def residual(self) -> float:
        return self.d["residual"]

    @property
    def points(self) -> list[dict]:
        return self.d["points"]

    def explained_variance(self) -> list[float]:
        return self.d["explained_variance_ratio"]

    def raw_scores(self, values: dict[str, float]) -> list[float]:
        """Unnormalized PCA scores — the space distances are measured in."""
        missing = [a for a in self.axis_ids if a not in values]
        if missing:
            raise ValueError(f"missing axes for projection: {missing[:5]}")
        x = np.array([values[a] for a in self.axis_ids], dtype=float)
        xs = (x - np.array(self.d["mean"])) / np.array(self.d["scale"])
        return [float(v) for v in (np.array(self.d["components"]) @ xs)]

    def project(self, values: dict[str, float]) -> CVector:
        """Project one segment's consensus axis values into C-space (display coords)."""
        scores = np.array(self.raw_scores(values))
        lo, hi = np.array(self.d["score_min"]), np.array(self.d["score_max"])
        span = np.where(hi - lo == 0, 1.0, hi - lo)
        coords = np.clip((scores - lo) / span, 0.0, 1.0)
        return CVector(coords=[round(float(v), 4) for v in coords], residual=self.residual)

    def neighbors(
        self, scores: list[float], *, k: int = 5, exclude: str | None = None
    ) -> list[Neighbor]:
        """Nearest fitted segments in **raw score space**. Distance there is naturally
        weighted by each factor's variance, so the dominant factors drive similarity —
        normalized [0,1] coords would give a near-zero-variance direction equal weight."""
        target = np.array(scores, dtype=float)
        out: list[Neighbor] = []
        for p in self.points:
            if exclude is not None and p["segment_id"] == exclude:
                continue
            dist = float(np.linalg.norm(np.array(p["scores"], dtype=float) - target))
            out.append(
                Neighbor(
                    segment_id=p["segment_id"], distance=round(dist, 4), profile=p.get("profile")
                )
            )
        return sorted(out, key=lambda n: n.distance)[:k]

    def twin_ranks(self) -> list[dict]:
        """For each member of a twin pair (same structural profile, different scene), the
        rank of its twin among all other fitted segments by distance — 1 means the twin is
        the nearest neighbour. Unlike a nearest-neighbour hit rate, a rank stays comparable
        as the corpus grows: a denser space adds competitors for rank 1 without the
        instrument having changed."""
        groups: dict[str, list[dict]] = {}
        for p in self.points:
            if p.get("pair"):
                groups.setdefault(p["pair"], []).append(p)
        out: list[dict] = []
        for members in groups.values():
            if len(members) != 2:
                continue
            for me, twin in ((members[0], members[1]), (members[1], members[0])):
                order = self.neighbors(
                    me["scores"], k=len(self.points), exclude=me["segment_id"]
                )
                rank = [n.segment_id for n in order].index(twin["segment_id"]) + 1
                out.append(
                    {"segment_id": me["segment_id"], "twin": twin["segment_id"],
                     "rank": rank, "nearest": order[0].segment_id,
                     "nearest_distance": order[0].distance}
                )
        return sorted(out, key=lambda r: r["segment_id"])

    # --- persistence ---
    def save(self, path: Path | None = None) -> Path:
        p = path or default_model_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.d, indent=2), encoding="utf-8")
        return p

    @classmethod
    def load(cls, path: Path | None = None) -> ProjectionModel | None:
        p = path or default_model_path()
        if not p.exists():
            return None
        return cls(json.loads(p.read_text(encoding="utf-8")))


# ---- fitting from stored ratings ----------------------------------------------------


def scalar_axes(axes: list[AxisDef]) -> list[AxisDef]:
    return [a for a in axes if a.kind == "scalar"]


def fit_from_storage(
    axes: list[AxisDef] | None = None, *, source: str = "pilot",
    axes_version: int | None = None,
) -> ProjectionModel:
    """Fit over every rated segment whose frontmatter `source` matches (the pilot corpus).
    All consensus values come from ONE `axes_version` cohort (default: the registry's
    current version) — a frame fitted across anchor revisions would pool incomparable
    scores — and from ONE rater panel (`consensus_panel`), so a rater with partial
    coverage never shifts the segments it happened to score. Both are recorded in the
    model for provenance."""
    axes = axes or load_axes()
    if axes_version is None:
        axes_version = load_axes_version()
    sc = scalar_axes(axes)
    axis_ids = [a.id for a in sc]
    axis_names = {a.id: a.name for a in sc}

    segs = [s for s in storage.list_segments() if s.get("source") == source]
    rated_by = [
        set(storage.latest_ratings(s["id"], axes_version=axes_version)) for s in segs
    ]
    rated_by = [r for r in rated_by if r]
    all_raters = sorted(set().union(*rated_by)) if rated_by else []
    panel = consensus_panel(
        {r: sum(r in rb for rb in rated_by) / len(rated_by) for r in all_raters}
    )
    rows: list[list[float]] = []
    kept: list[dict] = []
    for s in sorted(segs, key=lambda d: d["id"]):
        vals = consensus_for_segment(
            s["id"], axis_ids, axes_version=axes_version, raters=panel
        )
        if vals is None:
            continue
        seg = storage.load_segment(s["id"]) or {}
        rows.append([vals[a] for a in axis_ids])
        kept.append({"id": s["id"], "profile": seg.get("profile"), "pair": seg.get("pair")})
    if len(rows) < 2:
        raise ValueError(
            f"need >=2 rated '{source}' segments to fit (found {len(rows)} "
            f"under axes_version {axes_version})"
        )
    model = ProjectionModel.fit(np.array(rows), axis_ids, axis_names, kept)
    model.d["axes_version"] = axes_version
    model.d["raters"] = panel
    return model


def project_segment(model: ProjectionModel, segment_id: str) -> CVector | None:
    vals = consensus_for_segment(
        segment_id,
        model.axis_ids,
        axes_version=model.d.get("axes_version"),
        raters=model.d.get("raters"),
    )
    if vals is None:
        return None
    return model.project(vals)
