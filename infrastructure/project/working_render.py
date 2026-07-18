"""Batch core-pipeline render and audit for projects under ``projects/working/``."""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from infrastructure.core.files.pdf_locator import find_combined_pdf as locate_combined_pdf
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.validation.content.pdf_validator import validate_pdf_rendering

WORKING_DIR = "projects/working"
REQUIRED_MARKERS = ("tests", "manuscript")


@dataclass
class ProjectAudit:
    """Per-project render audit record."""

    name: str
    status: str
    pipeline_success: bool
    duration_sec: float
    failing_stage: str | None = None
    failing_stage_num: int | None = None
    error_message: str = ""
    top_pdf: str | None = None
    local_pdf: str | None = None
    top_pdf_bytes: int = 0
    pdf_validation_ok: bool | None = None
    pdf_validation_issues: int | None = None
    structure_ok: bool = True
    structure_notes: list[str] = field(default_factory=list)
    log_path: str | None = None
    stages: list[dict[str, object]] = field(default_factory=list)


def list_working_projects(repo: Path) -> list[str]:
    """Return sorted project names under ``projects/working/``."""
    root = repo / WORKING_DIR
    if not root.is_dir():
        return []
    names: list[str] = []
    for child in sorted(root.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir() or child.is_symlink():
            names.append(child.name)
    return names


def has_manuscript(project_dir: Path) -> bool:
    """Return True when *project_dir* holds a ``manuscript/`` dir with ``*.md`` files."""
    manuscript = project_dir / "manuscript"
    return manuscript.is_dir() and any(manuscript.glob("*.md"))


def _combined_pdf_path(output_dir: Path, project_name: str) -> Path | None:
    """Resolve a combined PDF under *output_dir* using the shared locator."""
    search_root = output_dir.parent if output_dir.name == "pdf" else output_dir
    located = locate_combined_pdf(search_root, project_name)
    return located[0] if located else None


def check_structure(project_dir: Path) -> tuple[bool, list[str]]:
    """Verify minimum WIP structure (tests + manuscript; src optional but noted)."""
    notes: list[str] = []
    for marker in REQUIRED_MARKERS:
        if not (project_dir / marker).is_dir():
            notes.append(f"missing {marker}/")
    if not (project_dir / "src").is_dir():
        notes.append("missing src/")
    return len(notes) == 0 or (len(notes) == 1 and notes == ["missing src/"]), notes


def stage_summaries(results: list[PipelineStageResult]) -> list[dict[str, object]]:
    """Serialize stage results for the audit JSON."""
    return [
        {
            "stage_num": r.stage_num,
            "stage_name": r.stage_name,
            "success": r.success,
            "duration_sec": round(r.duration, 2),
            "exit_code": r.exit_code,
            "error_message": r.error_message,
        }
        for r in results
    ]


def first_failure(results: list[PipelineStageResult]) -> tuple[int | None, str | None, str]:
    """Return (stage_num, stage_name, error_message) for the first failed stage."""
    for result in results:
        if not result.success:
            return result.stage_num, result.stage_name, result.error_message
    return None, None, ""


def classify_status(
    *,
    pipeline_success: bool,
    top_pdf: Path | None,
    local_pdf: Path | None,
    structure_ok: bool,
    pdf_validation_ok: bool | None,
) -> str:
    """Assign PASS / PARTIAL / FAIL-* status per working-render rubric."""
    if not structure_ok:
        return "FAIL — structure"
    if pipeline_success and top_pdf is not None and top_pdf.stat().st_size > 0:
        if pdf_validation_ok is False:
            return "PARTIAL — PDF validation issues"
        return "PASS — full top-level PDF"
    if local_pdf is not None and local_pdf.stat().st_size > 0:
        return "PARTIAL — local PDF only"
    return "FAIL — pipeline"


def failure_category(failing_stage: str | None) -> str:
    """Map failing stage name to rubric category suffix."""
    if failing_stage is None:
        return "pipeline"
    name = failing_stage.lower()
    if "test" in name:
        return "tests"
    if "analysis" in name:
        return "analysis"
    if "pdf" in name or "render" in name:
        return "render"
    if "copy" in name or "valid" in name:
        return "copy/validate"
    return "pipeline"


def run_project_pipeline(
    repo: Path,
    name: str,
    *,
    skip_infra: bool,
) -> tuple[list[PipelineStageResult], float]:
    """Execute core pipeline for one working project; return results and duration."""
    config = PipelineConfig(
        project_name=name,
        repo_root=repo,
        projects_dir=WORKING_DIR,
        skip_infra=skip_infra,
        skip_llm=True,
        resume=False,
        clean=True,
    )
    start = time.time()
    executor = PipelineExecutor(config)
    results = executor.execute_core_pipeline()
    return results, time.time() - start


def audit_project(
    repo: Path,
    name: str,
    results: list[PipelineStageResult],
    duration_sec: float,
) -> ProjectAudit:
    """Build audit record for one project from pipeline results."""
    project_dir = repo / WORKING_DIR / name
    structure_ok, structure_notes = check_structure(project_dir)
    pipeline_success = bool(results) and all(r.success for r in results)
    stage_num, stage_name, err_msg = first_failure(results)

    top_pdf = _combined_pdf_path(repo / "output" / name, name)
    local_pdf = _combined_pdf_path(project_dir / "output", name)
    log_path = project_dir / "output" / "logs" / "pipeline.log"

    pdf_validation_ok: bool | None = None
    pdf_issues: int | None = None
    if top_pdf is not None and top_pdf.stat().st_size > 0:
        try:
            report = validate_pdf_rendering(top_pdf)
            issues = report.get("issues", {})
            total = issues.get("total_issues", 0) if isinstance(issues, dict) else 0
            pdf_issues = int(total)
            pdf_validation_ok = total == 0
        except Exception as exc:  # noqa: BLE001 — record validation failure in audit
            pdf_validation_ok = False
            pdf_issues = -1
            err_msg = err_msg or f"PDF validation error: {exc}"

    status = classify_status(
        pipeline_success=pipeline_success,
        top_pdf=top_pdf,
        local_pdf=local_pdf,
        structure_ok=structure_ok
        and "missing tests/" not in structure_notes
        and "missing manuscript/" not in structure_notes,
        pdf_validation_ok=pdf_validation_ok,
    )
    if status.startswith("FAIL") and stage_name and status == "FAIL — pipeline":
        status = f"FAIL — {failure_category(stage_name)}"

    return ProjectAudit(
        name=name,
        status=status,
        pipeline_success=pipeline_success,
        duration_sec=round(duration_sec, 1),
        failing_stage=stage_name,
        failing_stage_num=stage_num,
        error_message=err_msg,
        top_pdf=str(top_pdf) if top_pdf else None,
        local_pdf=str(local_pdf) if local_pdf else None,
        top_pdf_bytes=top_pdf.stat().st_size if top_pdf and top_pdf.exists() else 0,
        pdf_validation_ok=pdf_validation_ok,
        pdf_validation_issues=pdf_issues,
        structure_ok=structure_ok,
        structure_notes=structure_notes,
        log_path=str(log_path) if log_path.exists() else None,
        stages=stage_summaries(results),
    )


def _classify_filesystem_only(audit: ProjectAudit) -> tuple[str, bool]:
    """PASS/PARTIAL/FAIL rubric for filesystem-only audits (no pipeline results).

    Distinct from :func:`classify_status` (which assumes pipeline-stage data): this
    rubric derives status from rendered-PDF presence and structure markers alone.
    """
    if audit.top_pdf and audit.pdf_validation_ok is True:
        return "PASS — full top-level PDF", True
    if audit.top_pdf:
        return "PARTIAL — PDF validation issues", False
    if audit.local_pdf:
        return "PARTIAL — local PDF only", False
    if audit.status.startswith("PASS"):
        return "PARTIAL — pipeline passed; top PDF missing", False
    if not audit.structure_ok or any(
        n.startswith("missing tests") or n.startswith("missing manuscript") for n in audit.structure_notes
    ):
        return "FAIL — structure", False
    return "FAIL — no PDF", False


def audit_project_filesystem_only(repo: Path, name: str) -> ProjectAudit:
    """Audit a working project from filesystem + PDF validator only (no pipeline run).

    Builds the standard audit record with empty pipeline results, then re-derives
    status via :func:`_classify_filesystem_only`. Backs the ``--audit-only`` path.
    """
    audit = audit_project(repo, name, results=[], duration_sec=0.0)
    audit.status, audit.pipeline_success = _classify_filesystem_only(audit)
    return audit


_PIPELINE_FAIL_RE = re.compile(r"Pipeline failed at stage (\d+):\s*([^—\n]+)")


def pipeline_log_failure(log_path: Path | None) -> tuple[int | None, str | None]:
    """Read the last ``PIPELINE_STAGE_FAILED`` line from a project pipeline log."""
    if log_path is None or not log_path.is_file():
        return None, None
    for line in reversed(log_path.read_text(encoding="utf-8", errors="replace").splitlines()):
        match = _PIPELINE_FAIL_RE.search(line)
        if match:
            return int(match.group(1)), match.group(2).strip()
    return None, None


def parse_batch_log_results(log_path: Path) -> dict[str, str]:
    """Parse ``Result: …`` lines from a tee'd batch log."""
    if not log_path.is_file():
        return {}
    pattern = re.compile(r"^Result: (.+?) \([\d.]+s\)")
    out: dict[str, str] = {}
    current: str | None = None
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("=== [") and "] " in line:
            part = line.split("] ", 1)[1].split(" (", 1)[0]
            current = part.split("/")[-1].strip() if "/" in part else part.strip()
        match = pattern.match(line.strip())
        if match and current:
            out[current] = match.group(1).strip()
    return out


def merge_batch_log_status(repo: Path, primary: Path | None) -> dict[str, str]:
    """Merge ``Result:`` lines from *primary* and known resume logs under ``output/``."""
    merged: dict[str, str] = {}
    paths: list[Path] = []
    if primary and primary.is_file():
        paths.append(primary)
    for name in ("_working_render_resume_small.log", "_working_render_resume_goldilocks.log"):
        candidate = repo / "output" / name
        if candidate.is_file() and candidate not in paths:
            paths.append(candidate)
    for path in paths:
        merged.update(parse_batch_log_results(path))
    return merged


def consolidate_audits(
    repo: Path,
    batch_log: Path | None,
    *,
    overrides: dict[str, ProjectAudit] | None = None,
) -> list[ProjectAudit]:
    """Build audits for all working projects using logs, overrides, and filesystem scan."""
    log_status = merge_batch_log_status(repo, batch_log)
    overrides = overrides or {}
    audits: list[ProjectAudit] = []
    for name in list_working_projects(repo):
        if name in overrides:
            audits.append(overrides[name])
            continue
        audit = audit_project(repo, name, [], 0.0)
        if name in log_status:
            audit.status = log_status[name]
            audit.pipeline_success = audit.status.startswith("PASS")
        # Log-derived PASS is stale if a later batch clean removed output/<name>/pdf/.
        if audit.status.startswith("PASS") and not audit.top_pdf:
            if audit.local_pdf:
                audit.status = "PARTIAL — local PDF only (top output missing)"
            else:
                audit.status = "PARTIAL — pipeline passed; top PDF missing"
            audit.pipeline_success = False
        stage_num, stage_name = pipeline_log_failure(Path(audit.log_path) if audit.log_path else None)
        if stage_name and audit.failing_stage is None and not audit.status.startswith("PASS"):
            audit.failing_stage = stage_name
            audit.failing_stage_num = stage_num
        audits.append(audit)
    return audits


def write_audit_report(repo: Path, audits: list[ProjectAudit]) -> tuple[Path, Path]:
    """Write JSON audit and markdown summary under ``output/``."""
    output_dir = repo / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "_working_render_audit.json"
    md_path = output_dir / "_working_render_audit.md"

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "projects_dir": WORKING_DIR,
        "project_count": len(audits),
        "pass_count": sum(1 for audit in audits if audit.status.startswith("PASS")),
        "partial_count": sum(1 for audit in audits if audit.status.startswith("PARTIAL")),
        "fail_count": sum(1 for audit in audits if audit.status.startswith("FAIL")),
        "projects": [asdict(audit) for audit in audits],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Working projects render audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "| Project | Status | Duration | Failing stage | Top PDF |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for audit in audits:
        fail = audit.failing_stage or "—"
        top = "yes" if audit.top_pdf else "no"
        lines.append(f"| {audit.name} | {audit.status} | {audit.duration_sec}s | {fail} | {top} |")
    lines.extend(["", "## Log pointers", ""])
    for audit in audits:
        if audit.log_path:
            lines.append(f"- **{audit.name}**: `{audit.log_path}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


__all__ = [
    "ProjectAudit",
    "WORKING_DIR",
    "audit_project",
    "audit_project_filesystem_only",
    "check_structure",
    "has_manuscript",
    "classify_status",
    "failure_category",
    "first_failure",
    "list_working_projects",
    "consolidate_audits",
    "merge_batch_log_status",
    "parse_batch_log_results",
    "pipeline_log_failure",
    "run_project_pipeline",
    "stage_summaries",
    "write_audit_report",
]
