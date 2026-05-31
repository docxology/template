"""Active Inference Ontology bindings and concordance helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from gnn.concordance import BERNOULLI_EXPECTED_TERMS, BERNOULLI_SYMBOL_MAP, parity_gaps
from gnn.parser import parse_gnn_file

SI_SYMBOL_MAP: dict[str, str] = {
    "location": "loc",
    "observation": "obs",
    "policy": "pi",
    "belief_entropy": "belief_entropy",
}

SI_EXPECTED_TERMS: dict[str, str] = {
    "loc": "HiddenState",
    "obs": "ObservationLikelihood",
    "pi": "PolicyPosterior",
    "belief_entropy": "BeliefEntropy",
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


def validate_gnn_ontology(
    gnn_path: Path,
    symbol_map: dict[str, str] | None = None,
    *,
    expected_terms: dict[str, str] | None = None,
    label: str | None = None,
) -> list[str]:
    model = parse_gnn_file(gnn_path)
    terms = expected_terms if expected_terms is not None else BERNOULLI_EXPECTED_TERMS
    gaps: list[str] = parity_gaps(model, symbol_map or BERNOULLI_SYMBOL_MAP, expected_terms=terms)
    prefix = label or gnn_path.stem
    return [f"{prefix}: {gap}" for gap in gaps]


def _validate_section_ontology_exact(
    *,
    section_path: Path,
    expected_terms: dict[str, str],
    label: str,
) -> list[str]:
    section_terms = load_section_ontology(section_path)
    gaps: list[str] = []
    for variable, expected in expected_terms.items():
        actual = section_terms.get(variable)
        if actual != expected:
            gaps.append(f"{label}: section ontology variable {variable!r} annotated {actual!r}, expected {expected!r}")
    for variable in sorted(set(section_terms) - set(expected_terms)):
        gaps.append(f"{label}: section ontology variable {variable!r} is not mapped by the expected model terms")
    return gaps


def validate_all_gnn_ontology(project_root: Path) -> list[str]:
    """Validate every project GNN model against its model-specific ontology map."""
    root = project_root.resolve()
    checks = (
        (
            root / "gnn" / "bernoulli_toy.gnn.md",
            root / "manuscript" / "sections" / "imrad" / "methods_analytical" / "ontology.yaml",
            BERNOULLI_SYMBOL_MAP,
            BERNOULLI_EXPECTED_TERMS,
            "bernoulli_toy",
        ),
        (
            root / "gnn" / "si_tmaze.gnn.md",
            root / "manuscript" / "sections" / "imrad" / "methods_pymdp" / "ontology.yaml",
            SI_SYMBOL_MAP,
            SI_EXPECTED_TERMS,
            "si_tmaze",
        ),
    )
    gaps: list[str] = []
    for path, section_path, symbol_map, expected_terms, label in checks:
        if not path.is_file():
            gaps.append(f"{label}: missing {path.relative_to(root)}")
            continue
        gaps.extend(
            validate_gnn_ontology(
                path,
                symbol_map,
                expected_terms=expected_terms,
                label=label,
            )
        )
        gaps.extend(
            _validate_section_ontology_exact(
                section_path=section_path,
                expected_terms=expected_terms,
                label=label,
            )
        )
    return gaps
