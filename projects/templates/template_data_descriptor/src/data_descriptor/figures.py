"""Figure-data preparers for the data-descriptor exemplar.

These functions compute *plot-ready* data structures (table rows, ordered
steps, severity counts) from a descriptor mapping but never import matplotlib.
The sibling :mod:`data_descriptor.figure_pipeline` module renders these values;
keeping preparation separate makes every data transformation directly testable
without a display backend while the script remains a genuine thin entry point.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Any

from data_descriptor.descriptor import summarize_field_constraints, validate_descriptor
from data_descriptor.verification import FileVerification


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


@dataclass(frozen=True)
class DescriptorFigureSpec:
    """Provenance metadata for one generated manuscript figure."""

    label: str
    filename: str
    caption: str
    generated_by: str
    alt_text: str


FIGURE_REGISTRY_SCHEMA = "template-data-descriptor-figure-registry-v1"
DESCRIPTOR_FIGURE_SPECS: tuple[DescriptorFigureSpec, ...] = (
    DescriptorFigureSpec(
        label="fig:schema_overview",
        filename="schema_overview.png",
        caption="Field schema and data dictionary generated from the descriptor.",
        generated_by="scripts.generate_figures.generate_figures",
        alt_text=(
            "Data-dictionary table encoding each declared field's type, nullability, unit, and constraint; "
            "the table describes metadata rather than observed values."
        ),
    ),
    DescriptorFigureSpec(
        label="fig:file_inventory",
        filename="file_inventory.png",
        caption="Declared row counts for every file in the descriptor inventory.",
        generated_by="scripts.generate_figures.generate_figures",
        alt_text=(
            "Horizontal bars encode descriptor-declared row counts by file; declared counts alone do not "
            "establish that the corresponding bytes are present or verified."
        ),
    ),
    DescriptorFigureSpec(
        label="fig:provenance_flow",
        filename="provenance_flow.png",
        caption="Ordered provenance steps and their responsible agents.",
        generated_by="scripts.generate_figures.generate_figures",
        alt_text=(
            "Connected boxes encode descriptor-declared provenance steps and responsible agents from left to "
            "right; the diagram records the claim and does not independently verify execution."
        ),
    ),
    DescriptorFigureSpec(
        label="fig:quality_gate",
        filename="quality_gate.png",
        caption="Validation findings for the clean fixture and deliberately broken control.",
        generated_by="scripts.generate_figures.generate_figures",
        alt_text=(
            "Grouped bars compare descriptor-validation error and warning counts for the supplied descriptor "
            "and an explicitly synthetic broken control."
        ),
    ),
    DescriptorFigureSpec(
        label="fig:checksum_verification",
        filename="checksum_verification.png",
        caption="Declared and recomputed row counts and checksum status by file.",
        generated_by="scripts.generate_figures.generate_figures",
        alt_text=(
            "Verification table encoding declared versus recomputed row counts, checksum agreement, and status "
            "for each file; readiness is a descriptor-validation score, not a scientific quality score."
        ),
    ),
)
_FIGURE_SPEC_BY_LABEL = {spec.label: spec for spec in DESCRIPTOR_FIGURE_SPECS}


def descriptor_figure_spec(label: str) -> DescriptorFigureSpec:
    """Return the canonical generated-figure specification for ``label``."""
    try:
        return _FIGURE_SPEC_BY_LABEL[label]
    except KeyError as exc:
        raise KeyError(f"unknown descriptor figure label: {label!r}") from exc


def descriptor_figure_specs_for_data(
    descriptor: dict[str, Any],
    checks: Iterable[FileVerification],
    *,
    readiness_score: float,
) -> tuple[DescriptorFigureSpec, ...]:
    """Bind registry descriptions to the descriptor and verification run.

    Args:
        descriptor: The same parsed descriptor used to render the figures.
        checks: The byte-level verification results rendered in the table.
        readiness_score: Descriptor report score shown in the table title.

    Returns:
        A complete specification tuple with data-derived alternate text.
    """
    check_rows = tuple(checks)
    clean = severity_counts(descriptor)
    broken = severity_counts(demo_broken_descriptor(descriptor))
    alt_by_label = {
        "fig:schema_overview": _schema_alt_text(schema_table_rows(descriptor)),
        "fig:file_inventory": _inventory_alt_text(file_inventory_rows(descriptor)),
        "fig:provenance_flow": _provenance_alt_text(provenance_steps(descriptor)),
        "fig:quality_gate": _quality_alt_text(clean, broken),
        "fig:checksum_verification": _verification_alt_text(check_rows, readiness_score),
    }
    return tuple(replace(spec, alt_text=alt_by_label[spec.label]) for spec in DESCRIPTOR_FIGURE_SPECS)


def _schema_alt_text(rows: tuple[SchemaRow, ...]) -> str:
    if not rows:
        return (
            "Empty data-dictionary table: the descriptor contains no renderable field entries, so no schema "
            "structure can be described."
        )
    fields = []
    for row in rows:
        details = [row.field_type or "type unspecified", f"nullable {row.nullable}"]
        if row.unit:
            details.append(f"unit {row.unit}")
        if row.constraint:
            details.append(f"constraint {row.constraint}")
        fields.append(f"{row.name or '(unnamed)'} ({', '.join(details)})")
    return (
        f"{len(rows)}-row data dictionary: {'; '.join(fields)}. The table describes declared metadata, not "
        "observed values."
    )


def _inventory_alt_text(rows: tuple[FileInventoryRow, ...]) -> str:
    if not rows:
        return (
            "Empty file-inventory bar chart: the descriptor contains no renderable file entries, so no "
            "declared row counts are available."
        )
    bars = "; ".join(f"{row.path or '(unnamed)'}: {row.rows}" for row in rows)
    largest = max(row.rows for row in rows)
    largest_paths = [row.path or "(unnamed)" for row in rows if row.rows == largest]
    return (
        f"{len(rows)} horizontal bars encode descriptor-declared row counts: {bars}. Largest declared count "
        f"{largest} occurs for {', '.join(largest_paths)}. Declared counts alone do not verify file bytes."
    )


def _provenance_alt_text(steps: tuple[ProvenanceStep, ...]) -> str:
    if not steps:
        return (
            "Empty provenance-flow panel: the descriptor contains no renderable provenance steps, so no "
            "processing chain is claimed."
        )
    nodes = " to ".join(f"{step.step or '(unnamed)'} ({step.agent or 'agent unspecified'})" for step in steps)
    return (
        f"{len(steps)} connected boxes run left to right: {nodes}. This is the descriptor-declared chain and "
        "does not independently verify that the steps ran."
    )


def _quality_alt_text(clean: dict[str, int], broken: dict[str, int]) -> str:
    return (
        "Grouped bars compare validation findings. Supplied descriptor: "
        f"{clean.get('error', 0)} errors and {clean.get('warning', 0)} warnings. Deliberately perturbed "
        f"control: {broken.get('error', 0)} errors and {broken.get('warning', 0)} warnings. The control is "
        "synthetic and demonstrates gate sensitivity; it is not an empirical data-quality estimate."
    )


def _verification_alt_text(checks: tuple[FileVerification, ...], readiness_score: float) -> str:
    if not checks:
        return (
            "Empty descriptor-to-file verification table: no file checks were available. Descriptor readiness "
            f"is {readiness_score:.3f}; that score does not establish byte integrity or scientific quality."
        )
    rows = verification_table_rows(checks)
    descriptions = [
        f"{path}: declared rows {declared}, actual rows {actual}, checksum {checksum}, status {status}"
        for path, declared, actual, checksum, status in rows
    ]
    return (
        f"{len(rows)}-row descriptor-to-file verification table: {'; '.join(descriptions)}. Descriptor "
        f"readiness is {readiness_score:.3f}; this is release-readiness evidence, not a scientific quality "
        "score."
    )


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


def verification_table_rows(
    checks: Iterable[FileVerification],
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Return display rows for descriptor-to-file verification results."""
    rows: list[tuple[str, str, str, str, str]] = []
    for check in checks:
        actual = "—" if check.actual_rows < 0 else str(check.actual_rows)
        checksum = "match" if check.checksum_ok else ("absent" if check.status == "absent" else "MISMATCH")
        rows.append((check.path, str(check.declared_rows), actual, checksum, check.status))
    return tuple(rows)


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
