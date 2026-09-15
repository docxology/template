"""Well-typed research contracts: typed block model, composition, checking.

A machine-checkable, compositional contract layer for manuscripts. The
structure is a preorder-enriched graph with monoidal composition (see
``model`` and ``compose`` docstrings); claims must be bound to evidence of
declared tier, formal statements must resolve, and the dependency graph
must be acyclic with all references resolvable.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ALL_BLOCK_TYPES",
    "Block",
    "Claim",
    "CompositionError",
    "Dataset",
    "DependencyEdge",
    "Derivation",
    "Diagnostic",
    "EdgeKind",
    "EMPTY_MANUSCRIPT",
    "Evidence",
    "EvidenceTier",
    "Figure",
    "FormalCode",
    "FormalStatement",
    "Manuscript",
    "MatchPolicy",
    "ReaderError",
    "Report",
    "Section",
    "Table",
    "check_manuscript",
    "compose",
    "compose_manuscripts",
    "read_blocks",
]

_EXPORTS = {
    "ALL_BLOCK_TYPES": ("infrastructure.formal_contracts.model", "ALL_BLOCK_TYPES"),
    "Block": ("infrastructure.formal_contracts.model", "Block"),
    "Claim": ("infrastructure.formal_contracts.model", "Claim"),
    "CompositionError": ("infrastructure.formal_contracts.checker", "CompositionError"),
    "Dataset": ("infrastructure.formal_contracts.model", "Dataset"),
    "DependencyEdge": ("infrastructure.formal_contracts.model", "DependencyEdge"),
    "Derivation": ("infrastructure.formal_contracts.model", "Derivation"),
    "Diagnostic": ("infrastructure.formal_contracts.checker", "Diagnostic"),
    "EdgeKind": ("infrastructure.formal_contracts.model", "EdgeKind"),
    "EMPTY_MANUSCRIPT": ("infrastructure.formal_contracts.checker", "EMPTY_MANUSCRIPT"),
    "Evidence": ("infrastructure.formal_contracts.model", "Evidence"),
    "EvidenceTier": ("infrastructure.formal_contracts.model", "EvidenceTier"),
    "Figure": ("infrastructure.formal_contracts.model", "Figure"),
    "FormalCode": ("infrastructure.formal_contracts.diagnostics", "FormalCode"),
    "FormalStatement": ("infrastructure.formal_contracts.model", "FormalStatement"),
    "Manuscript": ("infrastructure.formal_contracts.checker", "Manuscript"),
    "MatchPolicy": ("infrastructure.formal_contracts.model", "MatchPolicy"),
    "ReaderError": ("infrastructure.formal_contracts.reader", "ReaderError"),
    "Report": ("infrastructure.formal_contracts.checker", "Report"),
    "Section": ("infrastructure.formal_contracts.model", "Section"),
    "Table": ("infrastructure.formal_contracts.model", "Table"),
    "check_manuscript": ("infrastructure.formal_contracts.checker", "check_manuscript"),
    "compose": ("infrastructure.formal_contracts.checker", "compose"),
    "compose_manuscripts": ("infrastructure.formal_contracts.checker", "compose_manuscripts"),
    "read_blocks": ("infrastructure.formal_contracts.reader", "read_blocks"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)
