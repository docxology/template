"""Figure validation module - Validate figure registry against manuscript references.

This module provides utilities for validating that figure references in
manuscript files match the figure registry. Part of the infrastructure
layer (Layer 1) - reusable across all projects.
"""

import json
import re
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_substep, log_success

logger = get_logger(__name__)


_LATEX_FIGURE_REF_PATTERN = re.compile(r"\\(?:ref|label)\{(fig:[^}]+)\}")
_PANDOC_FIGURE_REF_PATTERN = re.compile(r"(?<![\w:-])@(fig:[-A-Za-z0-9_.:]+)")
_PANDOC_IMAGE_LABEL_PATTERN = re.compile(r"\{#(fig:[-A-Za-z0-9_.:]+)(?:\s[^}]*)?\}")
_FENCED_CODE_BLOCK_PATTERN = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
_INLINE_CODE_PATTERN = re.compile(r"`[^`\n]*`")
_SKIP_DOCS = frozenset(["AGENTS.md", "README.md"])


def _scan_manuscript_references(manuscript_dir: Path) -> set[str]:
    """Return all figure labels and references found in manuscript files."""
    referenced: set[str] = set()
    if not manuscript_dir.exists():
        return referenced
    for md_file in manuscript_dir.rglob("*.md"):
        if md_file.name in _SKIP_DOCS:
            continue
        try:
            text = _strip_reference_examples(
                "\n".join(line for line in md_file.read_text().splitlines() if not line.lstrip().startswith("%"))
            )
            referenced.update(_normalise_figure_label(label) for label in _LATEX_FIGURE_REF_PATTERN.findall(text))
            referenced.update(_normalise_figure_label(label) for label in _PANDOC_FIGURE_REF_PATTERN.findall(text))
            referenced.update(_normalise_figure_label(label) for label in _PANDOC_IMAGE_LABEL_PATTERN.findall(text))
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read {md_file.name}: {e}")
    return referenced


def _strip_reference_examples(text: str) -> str:
    """Remove code examples before scanning real manuscript references."""
    text = _FENCED_CODE_BLOCK_PATTERN.sub("", text)
    return _INLINE_CODE_PATTERN.sub("", text)


def _normalise_figure_label(label: str) -> str:
    """Drop trailing prose punctuation accidentally captured after @fig labels."""
    return label.rstrip(".,;:")


def _load_registry(registry_path: Path) -> tuple[dict[str, dict[str, object]] | None, str | None]:
    """Load the figure registry JSON; return (registry_entries, error_msg).

    Two shapes are accepted, both encoding the same set of figure labels:

    * **Dict shape** — keys are labels, values are figure metadata records
      (e.g. ``{"fig:convergence": {"caption": ..., "path": ...}, ...}``).
      Used by :class:`infrastructure.documentation.figure_manager.FigureManager`.
    * **Envelope shape** — a dict with a ``"figures"`` list whose items carry
      ``"label"`` fields (e.g. ``{"schema_version": ..., "figures": [...]}``).
      Used by project figure registries that also publish summary metadata.
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
        if isinstance(registry, dict) and isinstance(registry.get("figures"), list):
            registered = _registry_from_list_shape(registry["figures"])
        elif isinstance(registry, dict):
            registered = {str(label): item if isinstance(item, dict) else {} for label, item in registry.items()}
        elif isinstance(registry, list):
            registered = _registry_from_list_shape(registry)
        else:
            return None, (
                f"Failed to load figure registry: unexpected top-level JSON type "
                f"{type(registry).__name__} (expected object or array)"
            )
        log_success(f"Figure registry loaded: {len(registered)} figure(s)", logger)
        return registered, None
    except (OSError, json.JSONDecodeError, ValueError, AttributeError, TypeError, KeyError) as e:
        return None, f"Failed to load figure registry: {e}"


def _registry_from_list_shape(items: list[object]) -> dict[str, dict[str, object]]:
    """Return label-keyed registry entries from list-like figure records."""
    registered: dict[str, dict[str, object]] = {}
    unlabeled = 0
    for item in items:
        if isinstance(item, dict) and "label" in item:
            registered[str(item["label"])] = item
        else:
            unlabeled += 1
    if unlabeled:
        logger.warning(f"Figure registry has {unlabeled} item(s) without a 'label' field; skipped")
    return registered


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
        issue = f"Figure registry not found but {len(referenced_figures)} figure reference(s) found in manuscript"
        logger.warning(f"Figure registry not found at {registry_path}")
        logger.warning(f"  Found {len(referenced_figures)} figure reference(s) in manuscript")
        return False, [issue]

    registered_labels = set(registered_figures)
    issues = [f"Unregistered figure reference: {ref}" for ref in sorted(referenced_figures - registered_labels)]
    issues.extend(_missing_generated_figure_issues(registry_path, registered_figures, referenced_figures))

    if issues:
        logger.warning(f"  Found {len(issues)} figure issue(s)")
        for issue in issues:
            logger.warning(f"    • {issue}")
    else:
        log_success(f"All {len(referenced_figures)} figure references verified", logger)

    return len(issues) == 0, issues


def _missing_generated_figure_issues(
    registry_path: Path,
    registered_figures: dict[str, dict[str, object]],
    referenced_figures: set[str],
) -> list[str]:
    """Return missing-file issues for referenced generated registry entries."""
    issues: list[str] = []
    for label in sorted(referenced_figures & set(registered_figures)):
        record = registered_figures[label]
        filename = record.get("filename")
        if not isinstance(filename, str) or not filename:
            continue
        if "generated_by" not in record:
            continue
        figure_path = registry_path.parent / filename
        if not figure_path.exists():
            issues.append(f"Registered generated figure file is missing for {label}: {filename}")
    return issues
