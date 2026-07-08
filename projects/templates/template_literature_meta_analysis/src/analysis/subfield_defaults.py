"""Subfield default exports and modafinil keyword seed data."""

from __future__ import annotations

from pathlib import Path

import yaml

from analysis.subfield_registry import GENERIC_DEFAULT_SUBFIELDS

DEFAULT_SUBFIELDS: dict[str, dict] = GENERIC_DEFAULT_SUBFIELDS

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "subfield_defaults_modafinil.yaml"


def load_modafinil_subfield_keywords() -> dict[str, list[str]]:
    """Load modafinil subfield keywords from a file."""
    with open(_DATA_PATH, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    raw = data.get("subfields") or {}
    return {
        name: [str(keyword) for keyword in keywords] for name, keywords in raw.items() if isinstance(keywords, list)
    }
