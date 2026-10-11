"""Fixed original whole-PDF producer sequence under the existing live Source owner.

The outer worker selects the complete PDF contract after actual core execution.
This function retains that exact binding/diagnostic/failure order and receives
the same reader, pipeline identity, raw result and enclosing deadline. It never
creates an owner or infers Original authority from DATA.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def observe_whole_pdf_worker(
    root: Path,
    directory: Path,
    scope: str,
    formats: tuple[str, ...],
    native_reader: SnapshotReader,
    *,
    pipeline_run_id: str,
    plan_digest: str,
    run_id: str,
    deadline: float,
    env: dict[str, str],
    raw: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retain the fixed complete cohort and original controls; findings fail."""
    from infrastructure.reporting.native_pdf_whole_cohort import observe_whole_pdf_cohort
    from infrastructure.reporting.native_pdf_whole_control_supervisor import (
        supervise_whole_pdf_source_controls,
    )
    from infrastructure.reporting.native_pdf_whole_diagnostics import whole_pdf_diagnostics
    from infrastructure.reporting.native_format_acceptance_validation import _file

    raw["whole_pdf_cohort"] = observe_whole_pdf_cohort(
        root,
        directory / "whole-pdf-cohort",
        scope,
        formats,
        native_reader,
        pipeline_run_id=pipeline_run_id,
        plan_digest=plan_digest,
        env=env,
        deadline=deadline,
        run_id=run_id,
        candidate_rows=raw["artifacts"],
        candidate_tools=raw["tool_artifacts"],
        candidate_directory=directory,
    )
    cohort = _file(raw["whole_pdf_cohort"], native_reader).json_object()
    cohort_blockers, cohort_findings = whole_pdf_diagnostics(cohort, control_suite=False)
    raw["blockers"].extend(cohort_blockers)
    if cohort_findings:
        raise ValueError(f"actual whole PDF cohort failed: {cohort_findings}")
    raw["whole_pdf_source_controls"] = supervise_whole_pdf_source_controls(
        root,
        directory / "whole-pdf-source-controls",
        scope,
        formats,
        pipeline_run_id=pipeline_run_id,
        plan_digest=plan_digest,
        interpreter=Path(sys.executable),
        reader=native_reader,
        env=env,
        deadline=deadline,
        run_id=run_id,
    )
    controls = _file(raw["whole_pdf_source_controls"], native_reader).json_object()
    control_blockers, control_findings = whole_pdf_diagnostics(controls, control_suite=True)
    raw["blockers"].extend(control_blockers)
    if control_findings:
        raise ValueError(f"actual whole PDF controls failed: {control_findings}")
    return cohort, controls
