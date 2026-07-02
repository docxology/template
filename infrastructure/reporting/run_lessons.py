"""Run lesson reports for explicit pipeline learning."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from infrastructure.core.files.serialization import read_json_object as _read_json_object
from infrastructure.core.pipeline.types import PipelineStageResult


@dataclass(frozen=True)
class RunLesson:
    """One observed lesson from a pipeline run."""

    category: str
    stage_name: str
    stage_num: int
    severity: str
    message: str
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


@dataclass(frozen=True)
class RunLessonsWriteResult:
    """Paths written by ``write_run_lessons``."""

    jsonl_path: Path
    markdown_path: Path
    next_run_context_path: Path


def collect_run_lessons(
    results: Iterable[PipelineStageResult],
    *,
    project_output_dir: Path,
) -> list[RunLesson]:
    """Collect explicit lessons from stage results and HITL decisions."""
    lessons: list[RunLesson] = []
    for result in results:
        if not result.success:
            message = result.error_message or f"Stage exited with code {result.exit_code}"
            category = "hook_failure" if "hook" in message.lower() else "pipeline_failure"
            lessons.append(
                RunLesson(
                    category=category,
                    stage_name=result.stage_name,
                    stage_num=result.stage_num,
                    severity="error",
                    message=message,
                    source="pipeline",
                )
            )
        for message in result.lessons:
            lessons.append(
                RunLesson(
                    category="pipeline_note",
                    stage_name=result.stage_name,
                    stage_num=result.stage_num,
                    severity="info",
                    message=message,
                    source="pipeline",
                )
            )

    decisions_path = project_output_dir / "hitl" / "decisions.jsonl"
    if decisions_path.exists():
        lessons.extend(_lessons_from_decisions(decisions_path, project_output_dir=project_output_dir))
    lessons.extend(_lessons_from_artifact_manifest(project_output_dir / "reports" / "artifact_manifest.json"))
    lessons.extend(
        _lessons_from_pause_recommendations(
            project_output_dir / "reports" / "pause_recommendations.json",
            project_output_dir=project_output_dir,
        )
    )
    lessons.extend(
        _lessons_from_validation_report(
            project_output_dir / "reports" / "validation_report.json",
            project_output_dir=project_output_dir,
        )
    )
    lessons.extend(
        _lessons_from_telemetry(
            project_output_dir / "reports" / "telemetry.json", project_output_dir=project_output_dir
        )
    )
    return lessons


def write_run_lessons(
    project_output_dir: Path,
    lessons: Iterable[RunLesson],
) -> RunLessonsWriteResult:
    """Write ``output/reports/lessons.jsonl`` and ``lessons.md``."""
    report_dir = project_output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = report_dir / "lessons.jsonl"
    markdown_path = report_dir / "lessons.md"
    next_run_context_path = report_dir / "next_run_context.md"
    lesson_list = list(lessons)

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for lesson in lesson_list:
            fh.write(json.dumps(asdict(lesson), sort_keys=True) + "\n")

    markdown_path.write_text(_render_markdown(lesson_list), encoding="utf-8")
    next_run_context_path.write_text(_render_next_run_context(lesson_list), encoding="utf-8")
    return RunLessonsWriteResult(
        jsonl_path=jsonl_path,
        markdown_path=markdown_path,
        next_run_context_path=next_run_context_path,
    )


def _lessons_from_decisions(decisions_path: Path, *, project_output_dir: Path) -> list[RunLesson]:
    lessons: list[RunLesson] = []
    for line in decisions_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        action = str(row.get("action", ""))
        if action == "pause":
            continue
        stage_num = int(row.get("stage_num", 0) or 0)
        stage_name = str(row.get("stage_name", "") or f"stage-{stage_num:02d}")
        message = str(row.get("message", "") or action)
        lessons.append(
            RunLesson(
                category="human_intervention",
                stage_name=stage_name,
                stage_num=stage_num,
                severity="info" if action in {"approve", "guide", "resume"} else "warning",
                message=f"{action}: {message}",
                source=_release_safe_source(decisions_path, project_output_dir),
            )
        )
    return lessons


def _lessons_from_artifact_manifest(path: Path) -> list[RunLesson]:
    payload = _read_json_object(path)
    if not payload:
        return []
    lessons: list[RunLesson] = []
    for issue in payload.get("issues", []):
        lessons.append(
            RunLesson(
                category="artifact_drift",
                stage_name="artifact_manifest",
                stage_num=0,
                severity="warning",
                message=str(issue),
                source=_release_safe_source(path, path.parents[1]),
            )
        )
    return lessons


def _lessons_from_pause_recommendations(path: Path, *, project_output_dir: Path) -> list[RunLesson]:
    payload = _read_json_object(path)
    if not payload:
        return []
    lessons: list[RunLesson] = []
    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list):
        return lessons
    for row in recommendations:
        if not isinstance(row, dict):
            continue
        stage_num = int(row.get("stage_num", 0) or 0)
        lessons.append(
            RunLesson(
                category="pause_recommendation",
                stage_name=str(row.get("stage_name", "") or f"stage-{stage_num:02d}"),
                stage_num=stage_num,
                severity="info",
                message=str(row.get("reason", "") or row.get("message", "") or "pause recommended"),
                source=_release_safe_source(path, project_output_dir),
            )
        )
    return lessons


def _lessons_from_validation_report(path: Path, *, project_output_dir: Path) -> list[RunLesson]:
    payload = _read_json_object(path)
    if not payload:
        return []
    lessons: list[RunLesson] = []
    checks = payload.get("checks", {})
    if isinstance(checks, dict):
        for name, passed in checks.items():
            if passed is False:
                lessons.append(
                    RunLesson(
                        category="validation_defect",
                        stage_name="validation",
                        stage_num=0,
                        severity="warning",
                        message=f"{name} did not pass",
                        source=_release_safe_source(path, project_output_dir),
                    )
                )
    stats = payload.get("output_statistics", {})
    if isinstance(stats, dict):
        for key in ("evidence_issues", "artifact_manifest_issues"):
            values = stats.get(key)
            if isinstance(values, list):
                for value in values:
                    lessons.append(
                        RunLesson(
                            category="validation_defect",
                            stage_name="validation",
                            stage_num=0,
                            severity="warning",
                            message=str(value),
                            source=_release_safe_source(path, project_output_dir),
                        )
                    )
    return lessons


def _lessons_from_telemetry(path: Path, *, project_output_dir: Path) -> list[RunLesson]:
    payload = _read_json_object(path)
    if not payload:
        return []
    warnings = payload.get("warnings", [])
    if not isinstance(warnings, list):
        return []
    lessons: list[RunLesson] = []
    for row in warnings:
        if not isinstance(row, dict):
            continue
        lessons.append(
            RunLesson(
                category="slow_telemetry",
                stage_name=str(row.get("stage_name", "") or "telemetry"),
                stage_num=0,
                severity="warning",
                message=str(row.get("message", "") or row.get("warning_type", "") or "telemetry warning"),
                source=_release_safe_source(path, project_output_dir),
            )
        )
    return lessons


def _release_safe_source(path: Path, project_output_dir: Path) -> str:
    """Serialize report source paths relative to project output when possible."""
    try:
        return str(path.relative_to(project_output_dir))
    except ValueError:
        return path.name


def _render_markdown(lessons: list[RunLesson]) -> str:
    if not lessons:
        return "# Run Lessons\n\nNo run lessons recorded.\n"

    lines = ["# Run Lessons", ""]
    for lesson in lessons:
        lines.append(
            f"- **{lesson.category}** [{lesson.severity}] "
            f"stage {lesson.stage_num} ({lesson.stage_name}): {lesson.message}"
        )
    lines.append("")
    return "\n".join(lines)


def _render_next_run_context(lessons: list[RunLesson]) -> str:
    lines = [
        "# Next Run Context",
        "",
        "This report is advisory and is not automatically consumed by future runs.",
        "Use it only when explicitly deciding how to configure the next pipeline run.",
        "",
    ]
    if not lessons:
        lines.append("No lessons were recorded for the next run.")
        lines.append("")
        return "\n".join(lines)

    for lesson in lessons:
        lines.append(
            f"- [{lesson.severity}] {lesson.category}: stage {lesson.stage_num} "
            f"({lesson.stage_name}) - {lesson.message}"
        )
    lines.append("")
    return "\n".join(lines)
