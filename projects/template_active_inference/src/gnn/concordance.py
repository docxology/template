"""GNN ↔ ontology concordance checks."""

from __future__ import annotations

from gnn.model import GnnModel

BERNOULLI_SYMBOL_MAP: dict[str, str] = {
    "pi^1": "pi1",
    "pi^2": "pi2",
    "J": "J",
    "lambda": "lam",
    "gamma": "gamma",
    "q": "q_joint",
}


def parity_gaps(model: GnnModel, symbol_map: dict[str, str] | None = None) -> list[str]:
    mapping = symbol_map or BERNOULLI_SYMBOL_MAP
    gaps: list[str] = []
    for symbol, var in mapping.items():
        if not model.has(var):
            gaps.append(f"{symbol}: variable {var!r} not declared")
        elif var not in model.ontology:
            gaps.append(f"{symbol}: variable {var!r} has no Ontology annotation")
    return gaps


def concordance_holds(model: GnnModel, symbol_map: dict[str, str] | None = None) -> bool:
    return not parity_gaps(model, symbol_map)
