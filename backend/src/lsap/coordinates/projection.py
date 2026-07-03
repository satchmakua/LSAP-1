"""30 anchored axes --PCA--> the Literary Big Five C-space (DESIGN.md §4.2).

Label space. MAY depend on the `instrument` schema (read-only); the reverse is
forbidden. Fitted once over the rated corpus and persisted to `coordinates/model.json`.
Implemented in M3 (see ROADMAP.md).
"""

from __future__ import annotations

from pydantic import BaseModel

from lsap.instrument.schema import Rating  # allowed: coordinates reads instrument schema


class CVector(BaseModel):
    """A text's position in C-space; each component in [0, 1]."""

    c1_compression: float
    c2_narrative_structure: float
    c3_consciousness_depth: float
    c4_epistemic_stability: float
    c5_affective_intensity: float
    c6_residual: float  # the acknowledged remainder (Charter P5)


class ProjectionModel:
    def fit(self, ratings: list[Rating]) -> None:
        raise NotImplementedError("Implemented in M3 — see ROADMAP.md")

    def project(self, rating: Rating) -> CVector:
        raise NotImplementedError("Implemented in M3 — see ROADMAP.md")

    def explained_variance(self) -> list[float]:
        raise NotImplementedError("Implemented in M3 — see ROADMAP.md")
