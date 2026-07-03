"""Charter Principle 4 — the analysis/generation firewall, enforced as a build gate.

`lsap.engine` (generative space) must never import from `lsap.instrument` or
`lsap.coordinates` (analysis space). We parse the AST of every engine module rather
than importing it, so the check is robust to missing runtime deps.
"""

import ast
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1] / "src" / "lsap" / "engine"
FORBIDDEN = ("lsap.instrument", "lsap.coordinates", "instrument", "coordinates")


def _imported_modules(pyfile: Path) -> list[str]:
    tree = ast.parse(pyfile.read_text(encoding="utf-8"), filename=str(pyfile))
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def test_engine_never_imports_the_analysis_side():
    offenders: list[str] = []
    for pyfile in ENGINE_DIR.rglob("*.py"):
        for mod in _imported_modules(pyfile):
            if any(mod == f or mod.startswith(f + ".") for f in FORBIDDEN):
                offenders.append(f"{pyfile.name} imports '{mod}'")
    assert not offenders, "Firewall violation (Charter P4): " + "; ".join(offenders)
