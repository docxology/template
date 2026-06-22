"""Machine-readable registry of the repository's test suites.

The three suites (``infra_tests``, ``integration``, ``regression``) are
documented in prose across several READMEs, but an agent had no programmatic way
to discover them, their coverage floors, or their target packages — it had to
hand-construct ``pytest`` paths. This registry names that contract as data, so
verification (the "V" in an agent's build loop) becomes composable.

Pure data + lightweight dataclasses; importing this module has no side effects
and does not touch pytest's marker registration or the coverage gates.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SUITE_REGISTRY", "SuiteSpec", "get_suite_spec", "list_suites"]


@dataclass(frozen=True, slots=True)
class SuiteSpec:
    """One discoverable test suite."""

    name: str
    path: str
    description: str
    coverage_package: str | None
    coverage_floor: int | None
    default_markers_excluded: tuple[str, ...] = ()


SUITE_REGISTRY: dict[str, SuiteSpec] = {
    "infra_tests": SuiteSpec(
        name="infra_tests",
        path="tests/infra_tests",
        description="Infrastructure (Layer 1) unit/contract tests.",
        coverage_package="infrastructure",
        coverage_floor=60,
        default_markers_excluded=("requires_ollama", "slow", "bench", "private_project", "external_fixture"),
    ),
    "integration": SuiteSpec(
        name="integration",
        path="tests/integration",
        description="Cross-module integration tests exercising real pipelines end-to-end.",
        coverage_package=None,
        coverage_floor=None,
        default_markers_excluded=("requires_ollama", "slow"),
    ),
    "regression": SuiteSpec(
        name="regression",
        path="tests/regression",
        description="Claim-binding regression tier (scaffold-only until populated).",
        coverage_package=None,
        coverage_floor=None,
        default_markers_excluded=(),
    ),
}


def list_suites() -> list[str]:
    """Return all registered suite names."""
    return list(SUITE_REGISTRY)


def get_suite_spec(name: str) -> SuiteSpec:
    """Return the :class:`SuiteSpec` for ``name`` (raises ``KeyError`` if unknown)."""
    return SUITE_REGISTRY[name]
