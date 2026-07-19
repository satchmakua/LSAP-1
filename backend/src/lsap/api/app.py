"""The HTTP surface.

M0: health + the 30-axis registry. M1 adds rating: `POST /api/rate` (a segment → a
validated `Rating`, persisted) and read-back of stored segments/ratings.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lsap import storage
from lsap.coordinates import projection
from lsap.coordinates.projection import ProjectionModel
from lsap.engine import runtime as engine_runtime
from lsap.engine.compiler import Dials
from lsap.engine.presets import load_presets
from lsap.engine.runtime import EngineError, GenerationRun
from lsap.instrument import rater
from lsap.instrument.rater import RaterError
from lsap.instrument.schema import AxisDef, Rating, load_axes

app = FastAPI(title="LSAP-1 API", version="0.1.0")

# Local-first dev: the Vite dev server (localhost:5173) calls this on :8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_AXES: list[AxisDef] = load_axes()


def _hash_id(text: str) -> str:
    return "seg-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


class RateRequest(BaseModel):
    text: str
    title: str | None = None
    segment_id: str | None = None
    rater: str = "claude-opus-4-8"


class RateResponse(BaseModel):
    rating: Rating
    segment_id: str
    word_count: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "lsap-1", "axes_loaded": len(_AXES)}


@app.get("/api/axes")
def axes() -> list[AxisDef]:
    """The 30 observable-feature axes (blueprint §6)."""
    return _AXES


@app.post("/api/rate")
def rate_segment(req: RateRequest) -> RateResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    if req.segment_id:
        seg_id = req.segment_id
    elif req.title:
        seg_id = storage.slugify(req.title, fallback=_hash_id(text))
    else:
        seg_id = _hash_id(text)

    # Guard the id ↔ text link: a rating must correspond to the exact text it scored.
    # `save_segment` is write-once, so reusing an id for *different* text (a slug
    # collision, or an edit-then-re-rate) would orphan the new rating from its prose.
    # Reject before paying for a rating that would be mis-attributed.
    existing = storage.load_segment(seg_id)
    if existing is not None and str(existing.get("text", "")).strip() != text:
        raise HTTPException(
            status_code=409,
            detail=(
                f"segment id '{seg_id}' already stores different text — use a distinct "
                "title or segment_id (a revised text is a new segment)."
            ),
        )

    created_at = datetime.now(UTC).isoformat()
    try:
        rating = rater.rate(
            segment_id=seg_id,
            segment_text=text,
            rater=req.rater,
            axes=_AXES,
            created_at=created_at,
        )
    except RaterError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    storage.save_segment(seg_id, text, source=req.title or "pasted", created_at=created_at)
    storage.save_rating(rating)
    return RateResponse(rating=rating, segment_id=seg_id, word_count=storage.word_count(text))


@app.get("/api/segments")
def get_segments() -> list[dict]:
    return storage.list_segments()


@app.get("/api/segments/{segment_id}")
def get_segment(segment_id: str) -> dict:
    seg = storage.load_segment(segment_id)
    if seg is None:
        raise HTTPException(status_code=404, detail="segment not found")
    seg["ratings"] = [r.model_dump() for r in storage.load_ratings(segment_id)]
    return seg


# --- M3: the coordinate system -------------------------------------------------------


def _projection() -> ProjectionModel:
    model = ProjectionModel.load()
    if model is None:
        raise HTTPException(
            status_code=409,
            detail="no fitted projection — run `scripts/fit_projection.py` first",
        )
    return model


@app.get("/api/cspace")
def cspace() -> dict:
    """The fitted C-space map: factors (derived label + variance) and the corpus points."""
    m = _projection()
    return {
        "factors": m.factors,
        "residual": m.residual,
        "n_segments": m.d["n_segments"],
        "points": [
            {
                "segment_id": p["segment_id"],
                "profile": p.get("profile"),
                "pair": p.get("pair"),
                "coords": p["coords"],
            }
            for p in m.points
        ],
    }


@app.get("/api/segments/{segment_id}/projection")
def segment_projection(segment_id: str, k: int = 5) -> dict:
    """Project a rated segment into C-space and return its nearest corpus neighbours."""
    m = _projection()
    # Consensus from the cohort the frame was fitted on (older models carry no version
    # and fall back to the segment's newest) — never pooled across anchor revisions.
    values = projection.consensus_for_segment(
        segment_id, m.axis_ids, axes_version=m.d.get("axes_version")
    )
    if values is None:
        raise HTTPException(status_code=404, detail="segment has no ratings to project")
    nearest = m.neighbors(m.raw_scores(values), k=k, exclude=segment_id)
    return {
        "segment_id": segment_id,
        "vector": m.project(values).model_dump(),
        "neighbors": [n.model_dump() for n in nearest],
    }


# --- M4: the generative engine -------------------------------------------------------
# The API is the ONLY place the two halves meet, and even here they never call each
# other: the engine generates from operators + rules; re-rating its output is a separate,
# one-way trip back through /api/rate (Charter P4).


class GenerateRequest(BaseModel):
    dials: Dials
    situation: str
    paragraphs: int = 5


@app.get("/api/presets")
def presets() -> list[dict]:
    return [p.model_dump() for p in load_presets()]


@app.post("/api/generate")
def generate(req: GenerateRequest) -> GenerationRun:
    if not 1 <= req.paragraphs <= 8:
        raise HTTPException(status_code=400, detail="paragraphs must be between 1 and 8")
    try:
        return engine_runtime.generate(
            dials=req.dials, situation=req.situation, paragraphs=req.paragraphs
        )
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
