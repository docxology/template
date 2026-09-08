"""Import-lint guard: rendering must not import the publishing layer.

The rendering layer produces manuscripts; publishing distributes them. A
``rendering -> publishing`` import inverts that layering (publishing already
imports core and reporting-adjacent surfaces), so the direct dependency edge
is forbidden. The transmission family lives in ``infrastructure/transmission``
precisely so both layers can share it without an inversion
(``RENDERING-LAYERING-1``).

Known, documented exception: ``infrastructure.transmission.transmission_bookends``
imports four publishing modules (zenodo_urls, metadata_from_config,
publication_ledger, release_pairing) for its release-metadata bookend feature.
That edge is transmission -> publishing (documented in the transmission
README), never rendering -> publishing.
"""

from __future__ import annotations

import ast
import pathlib

RENDERING_ROOT = pathlib.Path(__file__).resolve().parents[3] / "infrastructure" / "rendering"

FORBIDDEN_MODULES = ("infrastructure.publishing", "infrastructure.reporting")


# No current exceptions. Rendering reaches publishing-side metadata via
# infrastructure.metadata (a shared leaf); new inversions must be re-homed,
# not allowlisted here.
_ALLOWED_EDGES = frozenset()


def _import_targets(tree: ast.AST) -> list[str]:
    """Return every absolute ``infrastructure.*`` module an AST imports."""
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            targets.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                targets.append(alias.name)
    return targets


def test_rendering_never_imports_publishing_or_reporting() -> None:
    """No ``infrastructure/rendering`` module imports publishing or reporting."""
    violations: list[str] = []
    for path in sorted(RENDERING_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for target in _import_targets(tree):
            if not target.startswith(FORBIDDEN_MODULES):
                continue
            edge = f"{path.relative_to(RENDERING_ROOT.parent.parent)}: {target}"
            if edge in _ALLOWED_EDGES:
                continue
            violations.append(edge)
    assert not violations, "rendering -> publishing/reporting inversion:\n" + "\n".join(violations)
