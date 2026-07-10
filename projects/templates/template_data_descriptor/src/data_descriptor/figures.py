"""Figure-data preparers for the data-descriptor exemplar.

These functions compute *plot-ready* data structures (table rows, ordered
steps, severity counts) from a descriptor mapping but never import matplotlib.
Rendering happens in the thin script under ``scripts/`` — keeping plotting out
of ``src/`` is the thin-orchestrator contract and makes every preparer
trivially testable without a display backend.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from data_descriptor.descriptor import summarize_field_constraints, validate_descriptor


@dataclass(frozen=True)
class SchemaRow:
    """One row of the field data-dictionary table.

    Attributes:
        name: Field name.
        field_type: Declared field type.
        nullable: Human-readable nullability (``"yes"`` / ``"no"``).
        unit: Declared unit, or ``""``.
        constraint: Compact human-readable constraint summary.
    """

    name: str
    field_type: str
    nullable: str
    unit: str
    constraint: str


@dataclass(frozen=True)
class FileInventoryRow:
    """One row of the file-inventory table/bar chart.

    Attributes:
        path: Descriptor-relative file path.
        rows: Declared row count.
        media_type: Declared media type.
    """

    path: str
    rows: int
    media_type: str


@dataclass(frozen=True)
class ProvenanceStep:
    """One node in the provenance flow.

    Attributes:
        index: Zero-based position in the chain.
        step: Step label.
        agent: Declared agent responsible for the step.
    """

    index: int
    step: str
    agent: str


def schema_table_rows(descriptor: dict[str, Any]) -> tuple[SchemaRow, ...]:
    """Build data-dictionary rows for the schema-overview figure.

    Args:
        descriptor: A parsed descriptor mapping.

    Returns:
        One :class:`SchemaRow` per declared field, in declaration order.
    """
    fields = descriptor.get("fields", [])
    summaries = {summary.name: summary for summary in summarize_field_constraints(descriptor)}
    rows: list[SchemaRow] = []
    if not isinstance(fields, list):
        return ()
    for field in fields:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", ""))
        summary = summaries.get(name)
        rows.append(
            SchemaRow(
                name=name,
                field_type=str(field.get("type", "")),
                nullable="yes" if field.get("nullable") else "no",
                unit=summary.unit if summary else str(field.get("unit", "")),
                constraint=_constraint_label(field, summary),
            )
        )
    return tuple(rows)


def file_inventory_rows(descriptor: dict[str, Any]) -> tuple[FileInventoryRow, ...]:
    """Build file-inventory rows for the inventory figure.

    Args:
        descriptor: A parsed descriptor mapping.

    Returns:
        One :class:`FileInventoryRow` per declared file, in declaration order.
    """
    files = descriptor.get("files", [])
    rows: list[FileInventoryRow] = []
    if not isinstance(files, list):
        return ()
    for item in files:
        if not isinstance(item, dict):
            continue
        rows.append(
            FileInventoryRow(
                path=str(item.get("path", "")),
                rows=int(item.get("rows", 0) or 0),
                media_type=str(item.get("media_type", "")),
            )
        )
    return tuple(rows)


def provenance_steps(descriptor: dict[str, Any]) -> tuple[ProvenanceStep, ...]:
    """Build ordered provenance steps for the provenance-flow figure.

    Args:
        descriptor: A parsed descriptor mapping.

    Returns:
        One :class:`ProvenanceStep` per declared provenance entry, in order.
    """
    provenance = descriptor.get("provenance", [])
    steps: list[ProvenanceStep] = []
    if not isinstance(provenance, list):
        return ()
    for index, entry in enumerate(provenance):
        if not isinstance(entry, dict):
            continue
        steps.append(
            ProvenanceStep(
                index=index,
                step=str(entry.get("step", "")),
                agent=str(entry.get("agent", "")),
            )
        )
    return tuple(steps)


def severity_counts(descriptor: dict[str, Any]) -> dict[str, int]:
    """Count validation findings by severity for the quality-gate figure.

    Args:
        descriptor: A parsed descriptor mapping.

    Returns:
        A mapping with ``error`` and ``warning`` finding counts.
    """
    findings = validate_descriptor(descriptor)
    return {
        "error": sum(1 for finding in findings if finding.severity == "error"),
        "warning": sum(1 for finding in findings if finding.severity == "warning"),
    }


def demo_broken_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    """Return a deliberately-perturbed copy used to demonstrate the quality gate.

    The perturbation is intentional and clearly named: it strips the license,
    corrupts a checksum, and removes a unit so the validator emits findings.
    It exists only to show, in a figure, that the gate reacts to defects; it is
    never treated as real data.

    Args:
        descriptor: A valid descriptor mapping to perturb.

    Returns:
        A deep-copied, deliberately-invalid descriptor.
    """
    broken = copy.deepcopy(descriptor)
    broken.pop("license", None)
    files = broken.get("files")
    if isinstance(files, list) and files and isinstance(files[0], dict):
        files[0]["checksum"] = "sha256:not-a-real-digest"
        files[0]["rows"] = 0
    fields = broken.get("fields")
    if isinstance(fields, list):
        for field in fields:
            if isinstance(field, dict) and field.get("type") == "number":
                field.pop("unit", None)
    broken["provenance"] = [{"step": "collect", "agent": "demo"}]
    return broken


def _constraint_label(field: dict[str, Any], summary: Any) -> str:
    constraints = field.get("constraints", {})
    if not isinstance(constraints, dict):
        return ""
    parts: list[str] = []
    minimum = constraints.get("minimum")
    maximum = constraints.get("maximum")
    if minimum is not None or maximum is not None:
        parts.append(f"[{minimum}, {maximum}]")
    allowed = constraints.get("allowed_values")
    if isinstance(allowed, list) and allowed:
        parts.append("{" + ", ".join(str(value) for value in allowed) + "}")
    pattern = constraints.get("pattern")
    if pattern:
        parts.append(f"pattern {pattern}")
    return "; ".join(parts)
