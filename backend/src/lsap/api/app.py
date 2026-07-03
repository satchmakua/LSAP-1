"""The HTTP surface. M0 serves health + the 30-axis registry (the seed of Rater Studio)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lsap.instrument.schema import AxisDef, load_axes

app = FastAPI(title="LSAP-1 API", version="0.1.0")

# Local-first dev: the Vite dev server (localhost:5173) calls this on :8000.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_AXES: list[AxisDef] = load_axes()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "lsap-1", "axes_loaded": len(_AXES)}


@app.get("/api/axes")
def axes() -> list[AxisDef]:
    """The 30 observable-feature axes (blueprint §6)."""
    return _AXES
