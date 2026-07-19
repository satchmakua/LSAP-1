"""Dial-a-preset configs, loaded from `presets.yaml` (data, not code — Charter P9).

FIREWALL: imports nothing from the analysis side.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from .compiler import Dials

PRESETS_PATH = Path(__file__).parent / "presets.yaml"


class Preset(BaseModel):
    id: str
    name: str
    description: str
    dials: Dials


def load_presets(path: Path = PRESETS_PATH) -> list[Preset]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Preset(**p) for p in data["presets"]]
