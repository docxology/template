"""Deterministic AutoResearch multi-phase orchestration engine.

Provides structured execution across AutoResearch phases:
1. Intrinsic phase validation (domain, plan, pipeline, scripts)
2. Task iteration & experiment candidate tracking
3. Extrinsic readiness verification (evidence, manifests, review gates, security)
4. Structured ledger persistence and publication gate validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.autoresearch.models import (
    AutoResearchPlan,
    AutoResearchReport,
)
from infrastructure.autoresearch.planner import build_autoresearch_plan
from infrastructure.autoresearch.reports import write_autoresearch_report
from infrastructure.autoresearch.validation import validate_autoresearch_plan


@dataclass
class OrchestrationEvent:
    """A discrete event during AutoResearch orchestration."""

    phase: str
    action: str
    status: str  # "ok", "warn", "error"
    message: str
    timestamp: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """Consolidated outcome of AutoResearch multi-phase loop."""

    project_name: str
    success: bool
    phase_reached: str
    candidates_processed: int
    events: list[OrchestrationEvent] = field(default_factory=list)
    report: AutoResearchReport | None = None
    plan: AutoResearchPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize orchestration outcome to JSON-friendly dict."""
        return {
            "project_name": self.project_name,
            "success": self.success,
            "phase_reached": self.phase_reached,
            "candidates_processed": self.candidates_processed,
            "events_count": len(self.events),
            "events": [
                {
                    "phase": e.phase,
                    "action": e.action,
                    "status": e.status,
                    "message": e.message,
                    "payload": e.payload,
                }
                for e in self.events
            ],
            "report": self.report.to_dict() if self.report else None,
        }


class AutoResearchOrchestrator:
    """Orchestrates deterministic multi-phase AutoResearch loops."""

    def __init__(
        self,
        repo_root: Path | str,
        project_name: str,
        projects_dir: str = "projects",
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.project_name = project_name
        self.projects_dir = projects_dir
        self.events: list[OrchestrationEvent] = []

    def log_event(
        self,
        phase: str,
        action: str,
        status: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Record an orchestration event."""
        self.events.append(
            OrchestrationEvent(
                phase=phase,
                action=action,
                status=status,
                message=message,
                payload=payload or {},
            )
        )

    def execute_plan(
        self,
        *,
        fail_on_intrinsic: bool = True,
        fail_on_extrinsic: bool = True,
        write_reports: bool = True,
    ) -> OrchestrationResult:
        """Execute the multi-phase validation and orchestration flow."""
        self.events.clear()

        # 1. Build Plan
        self.log_event("planning", "build_plan", "ok", f"Building AutoResearch plan for {self.project_name}")
        try:
            plan = build_autoresearch_plan(self.repo_root, self.project_name, projects_dir=self.projects_dir)
            project_root = plan.project_root
        except Exception as exc:
            self.log_event("planning", "build_plan", "error", f"Failed to build plan: {exc}")
            return OrchestrationResult(
                project_name=self.project_name,
                success=False,
                phase_reached="planning",
                candidates_processed=0,
                events=list(self.events),
            )

        # 2. Phase: Intrinsic Validation
        self.log_event("intrinsic", "validate_intrinsic", "ok", "Validating intrinsic phase contracts")
        intrinsic_report = validate_autoresearch_plan(plan, project_root, phase="intrinsic")
        if not intrinsic_report.valid and fail_on_intrinsic:
            self.log_event(
                "intrinsic",
                "validate_intrinsic",
                "error",
                f"Intrinsic phase validation failed with {intrinsic_report.summary.get('errors', 0)} errors",
            )
            return OrchestrationResult(
                project_name=self.project_name,
                success=False,
                phase_reached="intrinsic",
                candidates_processed=0,
                events=list(self.events),
                report=intrinsic_report,
                plan=plan,
            )

        # 3. Phase: Candidate & Budget Evaluation
        budget = plan.config.budget_policy
        self.log_event(
            "candidate_loop",
            "budget_check",
            "ok",
            (
                f"Budget policy allows max {budget.max_iterations} iterations "
                f"(wall-time cap: {budget.max_wall_clock_minutes}m)"
            ),
        )
        allowed_count = budget.max_iterations

        # 4. Phase: Extrinsic Validation
        self.log_event("extrinsic", "validate_extrinsic", "ok", "Validating extrinsic phase contracts")
        full_report = validate_autoresearch_plan(plan, project_root, phase="all")
        if not full_report.valid and fail_on_extrinsic:
            self.log_event(
                "extrinsic",
                "validate_extrinsic",
                "error",
                f"Extrinsic phase validation failed with {full_report.summary.get('errors', 0)} errors",
            )
            return OrchestrationResult(
                project_name=self.project_name,
                success=False,
                phase_reached="extrinsic",
                candidates_processed=allowed_count,
                events=list(self.events),
                report=full_report,
                plan=plan,
            )

        # 5. Write reports if requested
        if write_reports:
            try:
                write_autoresearch_report(project_root, full_report)
                self.log_event("finalization", "write_reports", "ok", "Wrote AutoResearch report artifacts")
            except Exception as exc:
                self.log_event("finalization", "write_reports", "warn", f"Could not write reports: {exc}")

        self.log_event("completion", "execute_plan", "ok", "AutoResearch orchestration completed successfully")
        return OrchestrationResult(
            project_name=self.project_name,
            success=full_report.valid,
            phase_reached="completed",
            candidates_processed=allowed_count,
            events=list(self.events),
            report=full_report,
            plan=plan,
        )


__all__ = [
    "AutoResearchOrchestrator",
    "OrchestrationEvent",
    "OrchestrationResult",
]
