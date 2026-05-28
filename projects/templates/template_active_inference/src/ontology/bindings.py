"""Active Inference Ontology bindings and concordance helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from gnn.concordance import BERNOULLI_SYMBOL_MAP, parity_gaps
from gnn.parser import parse_gnn_file

SI_SYMBOL_MAP: dict[str, str] = {
    "location": "loc",
    "observation": "obs",
    "policy": "pi",
    "belief_entropy": "belief_entropy",
}


def load_section_ontology(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    terms_block = data.get("terms")
    if isinstance(terms_block, dict):
        entries: dict[str, str] = {}
        for key, value in terms_block.items():
            if isinstance(value, dict):
                entries[str(key)] = str(value.get("label") or value.get("description") or key)
            else:
                entries[str(key)] = str(value)
        return entries
    return {str(k): str(v) for k, v in data.items()}


def validate_gnn_ontology(gnn_path: Path, symbol_map: dict[str, str] | None = None) -> list[str]:
    model = parse_gnn_file(gnn_path)
    gaps: list[str] = parity_gaps(model, symbol_map or BERNOULLI_SYMBOL_MAP)
    return gaps
