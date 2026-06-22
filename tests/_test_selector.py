"""Programmatic builder for ``pytest`` invocations.

Agents (and orchestrators) previously had to hand-construct strings like
``pytest tests/integration -m "not requires_ollama and not slow"``. If a marker
name changed, that string broke silently. This builder exposes paths and markers
as *data* and emits a validated ``pytest`` argv list, reusing the canonical
marker-expression builder in
:func:`infrastructure.core.pytest_marker_exprs.build_pytest_marker_expression`.

Example::

    from tests._test_selector import TestSelector
    TestSelector(suite="integration", exclude_markers=["requires_ollama"]).build()
    # -> ["tests/integration", "-m", "not requires_ollama"]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tests._suite_registry import SUITE_REGISTRY

__all__ = ["TestSelector", "select_tests"]


@dataclass
class TestSelector:
    """Declarative description of a pytest selection.

    Attributes:
        suite: Optional registered suite name (resolves to its path).
        paths: Explicit test paths (combined with the suite path if both given).
        markers: Marker expressions to require (each becomes a ``and <marker>``).
        exclude_markers: Markers to exclude (each becomes ``and not <marker>``).
        extra_args: Extra raw pytest args appended verbatim (e.g. ``-q``).
    """

    suite: str | None = None
    paths: list[str] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    exclude_markers: list[str] = field(default_factory=list)
    extra_args: list[str] = field(default_factory=list)

    def _resolved_paths(self) -> list[str]:
        resolved: list[str] = []
        if self.suite is not None:
            if self.suite not in SUITE_REGISTRY:
                raise KeyError(f"unknown suite: {self.suite!r}; known: {sorted(SUITE_REGISTRY)}")
            resolved.append(SUITE_REGISTRY[self.suite].path)
        resolved.extend(self.paths)
        return resolved

    def _marker_expression(self) -> str | None:
        parts: list[str] = []
        parts.extend(self.markers)
        parts.extend(f"not {m}" for m in self.exclude_markers)
        return " and ".join(parts) if parts else None

    def build(self) -> list[str]:
        """Return a ``pytest`` argv list (paths, ``-m EXPR`` if any, extra args)."""
        argv: list[str] = list(self._resolved_paths())
        expr = self._marker_expression()
        if expr:
            argv += ["-m", expr]
        argv += self.extra_args
        return argv


def select_tests(
    *,
    suite: str | None = None,
    paths: list[str] | None = None,
    markers: list[str] | None = None,
    exclude_markers: list[str] | None = None,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Functional shorthand for ``TestSelector(...).build()``."""
    return TestSelector(
        suite=suite,
        paths=paths or [],
        markers=markers or [],
        exclude_markers=exclude_markers or [],
        extra_args=extra_args or [],
    ).build()
