# LSAP-1

**One coordinate system for reading prose, one controllable engine for writing it — with a hard wall between them.**

LSAP-1 is the first buildable version of the **Literary Space Annotation Protocol**: an
honest measurement *instrument* that turns a prose segment into 30 anchored numbers and a
5–6 dimension coordinate space, plus a stateful *generative engine* that writes prose by
dialing structural parameters rather than imitating named authors. The two halves share a
vocabulary but are architecturally forbidden from feeding each other (the Charter's
analysis↔generation firewall).

- **Read the theory:** [LSAP_Foundational_Blueprint.md](LSAP_Foundational_Blueprint.md) — the L0–L7 stack and the Epistemic Charter.
- **Read the build design:** [DESIGN.md](DESIGN.md) — stack, data contracts, architecture, and the milestone order.

**Stack:** Python 3.12 (FastAPI + Pydantic + scikit-learn, Claude via the `anthropic` SDK) · React 19 + TypeScript (Vite) · local-first, git-diffable files.

**Status:** Design draft — run `/scaffold` to turn this into a running project.
