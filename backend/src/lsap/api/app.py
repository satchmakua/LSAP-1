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
