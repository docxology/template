"""Manuscript variable generation from the experiment tree.

The paper is the living record: every run-derived manuscript number comes
from the tree store via :mod:`template_experiment_tree.report` — never
hand-typed. ``generate_variables`` is the canonical hydration entrypoint
invoked by ``scripts/z_generate_manuscript_variables.py``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from template_experiment_tree.report import flatten_sections, render_variables
from template_experiment_tree.store import ExperimentStoreError, load_tree
from template_experiment_tree.tree import ExperimentTree


class ManuscriptVariablesError(ValueError):
    """Raised when manuscript variables cannot be generated from tree state."""


def generate_variables(
    tree_store: Path | str,
    output_path: Path | str,
    *,
    require_answered: bool = False,
) -> dict[str, Any]:
    """Build manuscript variables from the tree store and write them as JSON.

    Args:
        tree_store: Path to ``experiment_tree.json``.
        output_path: Destination for ``manuscript_variables.json``.
        require_answered: When True, fail if the tree has no answered nodes
            (the strict default for publication runs).

    Returns:
        The generated variables mapping.
    """
    try:
        tree = load_tree(tree_store)
    except ExperimentStoreError as exc:
        raise ManuscriptVariablesError(str(exc)) from exc
    if require_answered and not tree.has_answered():
        raise ManuscriptVariablesError("tree has no answered nodes and require_answered=True")

    variables: dict[str, Any] = dict(render_variables(tree))
    variables["exp_sections"] = flatten_sections(tree)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(variables, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return variables


def resolve_tokens(tokens: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    """Resolve ``{{TOKEN}}`` placeholders, failing closed on unbacked tokens.

    Raises:
        ManuscriptVariablesError: If a token has no tree-derived backing.
    """
    from template_experiment_tree.report import resolve_token_map as _resolve

    try:
        resolved: dict[str, Any] = dict(_resolve(tokens, variables))
        return resolved
    except KeyError as exc:
        raise ManuscriptVariablesError(str(exc)) from exc


def validate_tree(tree: ExperimentTree) -> None:
    """Re-run tree invariants (thin re-export for scripts)."""
    tree.validate()
