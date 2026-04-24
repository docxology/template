"""Figure validation module - Validate figure registry against manuscript references.

This module provides utilities for validating that figure references in
manuscript files match the figure registry. Part of the infrastructure
layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_substep, log_success

logger = get_logger(__name__)


_FIGURE_REF_PATTERN = re.compile(r"\\(?:ref|label)\{(fig:[^}]+)\}")
_SKIP_DOCS = frozenset(["AGENTS.md", "README.md"])


def _scan_manuscript_references(manuscript_dir: Path) -> set[str]:
    """Return all \\ref{fig:…} and \\label{fig:…} keys found in numbered manuscript files."""
    referenced: set[str] = set()
    if not manuscript_dir.exists():
        return referenced
    for md_file in manuscript_dir.glob("*.md"):
        if md_file.name in _SKIP_DOCS:
            continue
        try:
            referenced.update(_FIGURE_REF_PATTERN.findall(md_file.read_text()))
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {md_file.name}: {e}")
    return referenced


def _load_registry(registry_path: Path) -> tuple[set[str] | None, str | None]:
    """Load the figure registry JSON; return (registered_labels, error_msg).

    Two shapes are accepted, both encoding the same set of figure labels:

    * **Dict shape** — keys are labels, values are figure metadata records
      (e.g. ``{"fig:convergence": {"caption": ..., "path": ...}, ...}``).
      Used by :class:`infrastructure.documentation.figure_manager.FigureManager`.
    * **List shape** — each item is a record carrying a ``"label"`` field
      (e.g. ``[{"filename": ..., "label": "fig:foo"}, ...]``). Used by
      project scripts that emit a flat figure manifest.

    Items in the list shape that lack a ``"label"`` key are skipped with a
    warning rather than aborting validation. Any other top-level JSON type
    is reported as a load error.
    """
    if not registry_path.exists():
        return None, None  # absent, not broken
    try:
        with open(registry_path) as f:
            registry = json.load(f)
        if isinstance(registry, dict):
            registered = set(registry.keys())
        elif isinstance(registry, list):
            registered = set()
            unlabeled = 0
            for item in registry:
                if isinstance(item, dict) and "label" in item:
                    registered.add(item["label"])
                else:
                    unlabeled += 1
            if unlabeled:
                logger.warning(
                    f"Figure registry has {unlabeled} item(s) without a 'label' field; skipped"
                )
        else:
            return None, (
                f"Failed to load figure registry: unexpected top-level JSON type "
                f"{type(registry).__name__} (expected object or array)"
            )
        log_success(f"Figure registry loaded: {len(registered)} figure(s)", logger)
        return registered, None
    except (OSError, json.JSONDecodeError, ValueError, AttributeError, TypeError, KeyError) as e:
        return None, f"Failed to load figure registry: {e}"


def validate_figure_registry(registry_path: Path, manuscript_dir: Path) -> tuple[bool, list[str]]:
    """Validate figure registry against manuscript references.

    Checks that all figure references in manuscript markdown files are
    registered in the figure registry. Skips documentation files (AGENTS.md,
    README.md) when scanning for references.

    Args:
        registry_path: Path to figure registry JSON file
        manuscript_dir: Path to manuscript directory containing markdown files

    Returns:
        Tuple of (success, list of issues found):
        - success: True if all references are registered, False otherwise
        - issues: List of issue descriptions (empty if success is True)
    """
    log_substep("Validating figure registry...", logger)

    referenced_figures = _scan_manuscript_references(manuscript_dir)
    registered_figures, load_error = _load_registry(registry_path)

    if load_error:
        return False, [load_error]

    if not referenced_figures:
        return True, []

    if registered_figures is None:
        # Registry absent but figures are referenced
        issue = (
            f"Figure registry not found but {len(referenced_figures)} "
            f"figure reference(s) found in manuscript"
        )
        logger.warning(f"Figure registry not found at {registry_path}")
        logger.warning(f"  Found {len(referenced_figures)} figure reference(s) in manuscript")
        return False, [issue]

    issues = [f"Unregistered figure reference: {ref}" for ref in sorted(referenced_figures - registered_figures)]

    if issues:
        logger.warning(f"  Found {len(issues)} figure issue(s)")
        for issue in issues:
            logger.warning(f"    • {issue}")
    else:
        log_success(f"All {len(referenced_figures)} figure references verified", logger)

    return len(issues) == 0, issues
