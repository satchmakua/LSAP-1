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


def consensus_for_segment(
    segment_id: str, axis_ids: list[str], *, axes_version: int | None = None
) -> dict[str, float] | None:
    """Mean value per axis across raters — **newest** rating per rater, within one
    `axes_version` cohort (None = the segment's newest; cohorts are never pooled).
    None if unrated under that version."""
    latest = storage.latest_ratings(segment_id, axes_version=axes_version)
    if not latest:
        return None
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
    scores. The version is recorded in the model for provenance."""
    axes = axes or load_axes()
    if axes_version is None:
        axes_version = load_axes_version()
    sc = scalar_axes(axes)
    axis_ids = [a.id for a in sc]
    axis_names = {a.id: a.name for a in sc}

    segs = [s for s in storage.list_segments() if s.get("source") == source]
    rows: list[list[float]] = []
    kept: list[dict] = []
    for s in sorted(segs, key=lambda d: d["id"]):
        vals = consensus_for_segment(s["id"], axis_ids, axes_version=axes_version)
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
    return model


def project_segment(model: ProjectionModel, segment_id: str) -> CVector | None:
    vals = consensus_for_segment(
        segment_id, model.axis_ids, axes_version=model.d.get("axes_version")
    )
    if vals is None:
        return None
    return model.project(vals)
