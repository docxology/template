"""Advisory SmartPause recommendation scoring.

SmartPause is intentionally report-first. It computes reasons a human may want
to review a run, but the default pipeline does not pause on these scores.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.files.serialization import read_json_object as _read_json_object


@dataclass(frozen=True)
class PauseRecommendation:
    """One advisory pause recommendation."""

    stage_num: int
    stage_name: str
    score: float
    reason_codes: tuple[str, ...]
    evidence: tuple[str, ...] = ()
    suggested_action: str = "review"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe payload."""
        payload = asdict(self)
        payload["reason_codes"] = list(self.reason_codes)
        payload["evidence"] = list(self.evidence)
        return payload


def compute_pause_recommendations(project_output_dir: Path) -> list[PauseRecommendation]:
    """Compute advisory pause recommendations from current run reports."""
    reasons: dict[str, list[str]] = {}
    _collect_validation_reasons(project_output_dir / "reports" / "validation_report.json", reasons)
    _collect_autoresearch_reasons(project_output_dir / "reports" / "autoresearch_readiness.json", reasons)
    _collect_artifact_reasons(project_output_dir / "reports" / "artifact_manifest.json", reasons)
    _collect_telemetry_reasons(project_output_dir / "reports" / "telemetry.json", reasons)
    _collect_rejection_reasons(project_output_dir / "hitl" / "decisions.jsonl", reasons)

    recommendations: list[PauseRecommendation] = []
    for stage_name, evidence in sorted(reasons.items()):
        codes = tuple(_reason_code(line) for line in evidence)
        recommendations.append(
            PauseRecommendation(
                stage_num=_stage_num_for(stage_name, project_output_dir),
                stage_name=stage_name,
                score=float(len(set(codes))),
                reason_codes=tuple(dict.fromkeys(codes)),
                evidence=tuple(evidence),
                suggested_action="review before continuing",
            )
        )
    return sorted(recommendations, key=lambda item: item.score, reverse=True)


def write_pause_recommendations(
    project_output_dir: Path,
    recommendations: list[PauseRecommendation],
) -> Path:
    """Write ``output/reports/pause_recommendations.json``."""
    report_dir = project_output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "pause_recommendations.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "recommendations": [rec.to_dict() for rec in recommendations],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _collect_validation_reasons(path: Path, reasons: dict[str, list[str]]) -> None:
    payload = _read_json_object(path)
    if not payload:
        return
    checks = payload.get("checks", {})
    if isinstance(checks, dict):
        for name, passed in checks.items():
            if passed is False:
                reasons.setdefault(str(name), []).append(f"validation_failed: {name}")
    stats = payload.get("output_statistics", {})
    if isinstance(stats, dict):
        for issue in stats.get("evidence_issues", []) if isinstance(stats.get("evidence_issues"), list) else []:
            reasons.setdefault("Evidence registry", []).append(f"evidence_error: {issue}")
        for issue in (
            stats.get("design_validation_issues", []) if isinstance(stats.get("design_validation_issues"), list) else []
        ):
            reasons.setdefault("Project design overlays", []).append(f"design_validation: {issue}")


def _collect_artifact_reasons(path: Path, reasons: dict[str, list[str]]) -> None:
    payload = _read_json_object(path)
    if not payload:
        return
    for issue in payload.get("issues", []):
        reasons.setdefault("Artifact manifest", []).append(f"artifact_drift: {issue}")


def _collect_autoresearch_reasons(path: Path, reasons: dict[str, list[str]]) -> None:
    payload = _read_json_object(path)
    if not payload or payload.get("valid") is True:
        return
    issues = payload.get("issues", [])
    if not isinstance(issues, list):
        return
    for row in issues:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code", "AUTORESEARCH.READINESS"))
        message = str(row.get("message", "readiness issue"))
        reasons.setdefault("AutoResearch readiness", []).append(f"autoresearch_readiness: {code}: {message}")


def _collect_telemetry_reasons(path: Path, reasons: dict[str, list[str]]) -> None:
    payload = _read_json_object(path)
    if not payload:
        return
    warnings = payload.get("warnings", [])
    if not isinstance(warnings, list):
        return
    for row in warnings:
        if isinstance(row, dict):
            stage_name = str(row.get("stage_name", "") or "Telemetry")
            reasons.setdefault(stage_name, []).append(f"slow_telemetry: {row.get('message', row.get('warning_type'))}")


def _collect_rejection_reasons(path: Path, reasons: dict[str, list[str]]) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("action") == "reject":
            stage_name = str(row.get("stage_name", "") or "HITL")
            reasons.setdefault(stage_name, []).append(f"human_rejection: {row.get('message', '')}")


def _reason_code(text: str) -> str:
    return text.split(":", 1)[0]


def _stage_num_for(stage_name: str, project_output_dir: Path) -> int:
    decisions_path = project_output_dir / "hitl" / "decisions.jsonl"
    if not decisions_path.exists():
        return 0
    for line in decisions_path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("stage_name") == stage_name:
            return int(row.get("stage_num", 0) or 0)
    return 0
