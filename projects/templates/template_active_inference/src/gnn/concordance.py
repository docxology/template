"""GNN ↔ ontology concordance checks."""

from __future__ import annotations

from gnn.model import GnnModel

BERNOULLI_SYMBOL_MAP: dict[str, str] = {
    "pi^1": "pi1",
    "pi^2": "pi2",
    "E1": "E1",
    "E2": "E2",
    "J": "J",
    "lambda": "lam",
    "gamma": "gamma",
    "q": "q_joint",
}


# Canonical ontology terms for the Bernoulli-Ising toy variables. Pinned as a fixed
# reference so a relabel of bernoulli_toy.gnn.md to a different-but-valid term is caught
# by the production gate, not just by tests.
BERNOULLI_EXPECTED_TERMS: dict[str, str] = {
    "pi1": "Stream1PolicyVector",
    "pi2": "Stream2PolicyVector",
    "E1": "Stream1HabitPrior",
    "E2": "Stream2HabitPrior",
    "J": "CrossStreamCouplingPotential",
    "lam": "EntanglementDeformationParameter",
    "gamma": "SophisticationWeight",
    "q_joint": "EntangledJointPosterior",
}


def parity_gaps(
    model: GnnModel,
    symbol_map: dict[str, str] | None = None,
    expected_terms: dict[str, str] | None = None,
) -> list[str]:
    """Report concordance gaps between GNN symbols and their ontology annotations.

    By default this checks *presence* (variable declared + carries some Ontology
    annotation). When ``expected_terms`` (variable -> required ontology term) is
    supplied it additionally checks *correctness*: a variable silently re-annotated
    to a different-but-valid ontology term is caught, not waved through. This closes
    the "shape test passes on a relabel" gap.
    """
    mapping = symbol_map or BERNOULLI_SYMBOL_MAP
    gaps: list[str] = []
    for symbol, var in mapping.items():
        if not model.has(var):
            gaps.append(f"{symbol}: variable {var!r} not declared")
        elif var not in model.ontology:
            gaps.append(f"{symbol}: variable {var!r} has no Ontology annotation")
        elif expected_terms is not None and var in expected_terms and model.ontology[var] != expected_terms[var]:
            gaps.append(
                f"{symbol}: variable {var!r} annotated {model.ontology[var]!r}, expected {expected_terms[var]!r}"
            )
    return gaps


def concordance_holds(
    model: GnnModel,
    symbol_map: dict[str, str] | None = None,
    expected_terms: dict[str, str] | None = None,
) -> bool:
    return not parity_gaps(model, symbol_map, expected_terms)
