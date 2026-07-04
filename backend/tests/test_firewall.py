"""Charter Principle 4 — the analysis/generation firewall, enforced as a build gate.

`lsap.engine` (generative space) must never import from the analysis side
(`lsap.instrument`, `lsap.coordinates`, `lsap.storage`). We parse the AST of every
engine module rather than importing it, so the check is robust to missing runtime deps.

The scanner catches every import form: `import lsap.instrument`, `from lsap.x import y`,
`from lsap import instrument`, and relative `from .. import instrument`.
"""

import ast
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1] / "src" / "lsap" / "engine"
FORBIDDEN = (
    "lsap.instrument",
    "lsap.coordinates",
    "lsap.storage",
    "instrument",
    "coordinates",
    "storage",
)


def _imported_modules_from_source(source: str, filename: str = "<engine>") -> list[str]:
    tree = ast.parse(source, filename=filename)
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.append(node.module)
                mods += [f"{node.module}.{alias.name}" for alias in node.names]
            else:  # `from .. import instrument`
                mods += [alias.name for alias in node.names]
    return mods


def _imported_modules(pyfile: Path) -> list[str]:
    return _imported_modules_from_source(pyfile.read_text(encoding="utf-8"), str(pyfile))


def _is_forbidden(mod: str) -> bool:
    return any(mod == f or mod.startswith(f + ".") for f in FORBIDDEN)


def test_engine_never_imports_the_analysis_side():
    offenders: list[str] = []
    for pyfile in ENGINE_DIR.rglob("*.py"):
        for mod in _imported_modules(pyfile):
            if _is_forbidden(mod):
                offenders.append(f"{pyfile.name} imports '{mod}'")
    assert not offenders, "Firewall violation (Charter P4): " + "; ".join(offenders)


def test_scanner_catches_every_violation_form():
    # Each of these WOULD be a firewall violation if it appeared inside engine/.
    violations = [
        "import lsap.instrument",
        "import lsap.storage as s",
        "from lsap.instrument.schema import Rating",
        "from lsap.coordinates import projection",
        "from lsap import instrument",  # subpackage via `from lsap import X`
        "from lsap import storage, config",
        "from .. import coordinates",  # relative `from .. import X`
        "from ..instrument import schema",
    ]
    for src in violations:
        mods = _imported_modules_from_source(src)
        assert any(_is_forbidden(m) for m in mods), f"scanner missed: {src!r} -> {mods}"


def test_scanner_allows_innocent_imports():
    innocent = [
        "import os",
        "from pydantic import BaseModel",
        "from lsap import config",  # config is shared, not analysis-side
        "from lsap.engine.compiler import Dials",
    ]
    for src in innocent:
        mods = _imported_modules_from_source(src)
        assert not any(_is_forbidden(m) for m in mods), f"false positive: {src!r} -> {mods}"
