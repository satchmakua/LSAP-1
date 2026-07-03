# 2. The analysis/generation firewall (Charter Principle 4)

- **Status:** Accepted
- **Date:** 2026-07-02

## Context

LSAP-1 both *reads* prose (the instrument + coordinate system) and *writes* it (the
engine). The blueprint's Epistemic Charter, Principle 4, warns that if generation
reuses the analysis model, the system forms a self-confirming loop: "Hemingway-ish"
output strengthens the "Hemingway region," which produces more caricatured
"Hemingway-ish" output. The system drifts toward stylized caricature and away from
real literature. This is one of the project's three engineering pillars (DESIGN.md §1)
and the easiest to violate by accident, because the analysis C-space and the engine's
control sliders share names (C1–C5) for the writer's intuition.

## Decision

The generative package (`lsap.engine`) is **architecturally forbidden** from importing
the analysis packages (`lsap.instrument`, `lsap.coordinates`). The engine generates
from the operator basis (`operators.yaml`) and the constraint compiler; its `Dials`
are control inputs to operators B1–B5, computed by a path with **zero dependency** on
the instrument's fitted PCA. Generated prose *may* be evaluated by re-rating it through
the instrument (the sanctioned crossing, exposed only in the UI / an offline eval), but
that measurement **never feeds back into generation**.

The invariant is enforced as a build gate: `backend/tests/test_firewall.py` parses the
AST of every module under `engine/` and fails if any imports the analysis side.

## Consequences

- The wall is a test, not a habit — a violation breaks CI, not just a code review.
- Some duplication is accepted (e.g. the C1–C5 naming appears on both sides) rather
  than sharing a module across the boundary.
- Evaluating "did the slider actually change the prose?" requires an explicit,
  one-way, offline re-rating step — by design.
