"""Load default subfield keyword definitions from committed YAML."""

from __future__ import annotations
from pathlib import Path
import yaml

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "subfield_defaults_modafinil.yaml"


def load_default_subfields() -> dict[str, dict]:
    with open(_DATA_PATH, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    raw = data.get("subfields") or {}
    out: dict[str, dict] = {}
    for name, keywords in raw.items():
        out[name] = {"keywords": [str(k) for k in keywords]} if isinstance(keywords, list) else keywords
    return out


DEFAULT_SUBFIELDS: dict[str, dict] = load_default_subfields()
