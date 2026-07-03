# LSAP-1 backend

Python 3.11+ · FastAPI · Pydantic v2 · scikit-learn · Claude (`anthropic` SDK). Managed
with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # create venv + install deps
uv run uvicorn lsap.api.app:app --reload  # dev server on :8000
uv run pytest                             # tests
uv run ruff check .                       # lint
```

## Package map (mirrors DESIGN.md §5)

- `src/lsap/instrument/` — **L1** rater + the 30-axis registry (`axes.yaml`) and schema. *Interpretation space.*
- `src/lsap/coordinates/` — **L2/L3** PCA projection into the Literary Big Five C-space. *Label space.* May read `instrument` schema; never the reverse.
- `src/lsap/engine/` — **L6** operators, constraint compiler, runtime cognition. *Generative space.* **Imports nothing from `instrument`/`coordinates`** — the Charter P4 firewall, enforced by `tests/test_firewall.py`.
- `src/lsap/api/` — FastAPI adapters; the only place the three are wired to one process.
