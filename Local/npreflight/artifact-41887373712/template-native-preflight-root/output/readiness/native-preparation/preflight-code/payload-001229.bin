"""Typed phase residual DATA after genuine Original/Current native checks.

These graphs do not authenticate tools or grant coverage. The reader caller
projects actual checked predicates first. Original outcomes belong to Original;
extra Current obligations remain separate and constrain the full acceptance union.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

PHASE_RESIDUAL_SCHEMA = "template-native-oracle-phase-residual-graphs-v1"


def native_residual_rows(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for row in value:
        if (
            not isinstance(row, dict)
            or set(row)
            not in (
                {"id", "artifact_id", "axis", "reason"},
                {"id", "suite_id", "axis", "reason"},
            )
            or any(not isinstance(field, str) or not field for field in row.values())
        ):
            return False
    return True


def _graph(value: object, phase: str) -> tuple[dict[str, str], ...]:
    if not isinstance(value, list) or value and not native_residual_rows(value):
        raise ValueError("native " + phase + " residual graph changed its exact row fields")
    return tuple(dict(row) for row in cast(list[dict[str, str]], value))


@dataclass(frozen=True)
class NativeOracleResidualGraphs:
    """Complete Original graph and independently checked Original+Current graph."""

    scope: str
    source_binding: tuple[str, str]
    original_run_id: str
    artifact_contract_digest: str
    original: tuple[dict[str, str], ...]
    reader: tuple[dict[str, str], ...]

    def data(self) -> dict[str, Any]:
        """Retain both exact graphs for audit; no serialized capability exists."""
        return {
            "schema_version": PHASE_RESIDUAL_SCHEMA,
            "scope": self.scope,
            "source_binding": list(self.source_binding),
            "original_run_id": self.original_run_id,
            "artifact_contract_digest": self.artifact_contract_digest,
            "original": [dict(row) for row in self.original],
            "reader": [dict(row) for row in self.reader],
        }

    def combined(self) -> list[dict[str, str]]:
        """Keep the full checked joint graph, including ordered repeated gaps."""
        return [dict(row) for row in self.reader]


def reconcile_native_phase_residual_graphs(
    original: object,
    checked_reader: object,
    *,
    original_status: object,
    original_exit_code: object,
    scope: str,
    source_binding: tuple[str, str],
    original_run_id: str,
    artifact_contract_digest: str,
) -> NativeOracleResidualGraphs:
    """Preserve Original exactly while retaining additional actual reader gaps.

    Call only after the genuine reader's Source/SDK/process/control closing and
    fresh predicate projection. A required or serialized empty graph supplies
    no authority. Original rows must remain an exact ordered subsequence of
    that actual joint graph, including duplicate occurrences; no gap is dropped.
    """
    before, after = _graph(original, "Original"), _graph(checked_reader, "reader")
    if (
        original_status != ("blocked" if before else "pass")
        or type(original_exit_code) is not int
        or original_exit_code != (75 if before else 0)
    ):
        raise ValueError("native Original status/observed exit differs from its own residual graph")
    if (
        any(not isinstance(value, str) or not value for value in (scope, original_run_id, artifact_contract_digest))
        or not isinstance(source_binding, tuple)
        or len(source_binding) != 2
        or any(not isinstance(value, str) or not value for value in source_binding)
    ):
        raise ValueError("native phase residual graphs omitted their checked Source/run/artifact binding")
    remaining = iter(after)
    for row in before:
        if not any(candidate == row for candidate in remaining):
            raise ValueError("independent reader omitted, changed or reordered an Original residual")
    return NativeOracleResidualGraphs(scope, source_binding, original_run_id, artifact_contract_digest, before, after)
