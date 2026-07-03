"""The L1 rater — turns a prose segment into a validated `Rating` via Claude structured
output under the frozen manual. Implemented in M1 (see ROADMAP.md).

Interpretation space: this module must NEVER be imported by `lsap.engine`
(enforced by `tests/test_firewall.py`).
"""

from __future__ import annotations

from .schema import AxisDef, Rating


def rate(segment: str, rater_id: str, axes: list[AxisDef]) -> Rating:
    """Score `segment` on all 30 axes. Uses `client.messages.parse(...)` against the
    `Rating` schema so the result cannot come back malformed."""
    raise NotImplementedError("Implemented in M1 — see ROADMAP.md")
