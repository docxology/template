"""Deterministic AutoResearch multi-phase orchestration engine.

Provides structured execution across AutoResearch phases:
1. Intrinsic phase validation (domain, plan, pipeline, scripts)
2. Candidate budget evaluation (readiness-only; no candidate execution)
3. Extrinsic readiness verification (evidence, manifests, review gates, security)
4. Structured ledger persistence and publication gate validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    candidate_budget: int = 0
    reports_written: bool = False
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
            "candidate_budget": self.candidate_budget,
            "reports_written": self.reports_written,
            "events_count": len(self.events),
            "events": [
                {
                    "phase": e.phase,
                    "action": e.action,
                    "status": e.status,
                    "message": e.message,
                    "timestamp": e.timestamp,
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
                timestamp=datetime.now(timezone.utc).isoformat(),
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
        self.log_event("planning", "build_plan", "ok", f"Built AutoResearch plan for {self.project_name}")

        # 2. Phase: Intrinsic Validation
        intrinsic_report = validate_autoresearch_plan(plan, project_root, phase="intrinsic")
        if not intrinsic_report.valid:
            self.log_event(
                "intrinsic",
                "validate_intrinsic",
                "error" if fail_on_intrinsic else "warn",
                f"Intrinsic phase validation failed with {intrinsic_report.summary.get('errors', 0)} errors",
            )
        else:
            self.log_event("intrinsic", "validate_intrinsic", "ok", "Intrinsic phase contracts passed")
        if not intrinsic_report.valid and fail_on_intrinsic:
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
                f"(wall-time cap: {budget.max_wall_clock_minutes}m); readiness mode executes no candidates"
            ),
            payload={"candidate_budget": budget.max_iterations, "candidates_processed": 0},
        )
        candidate_budget = budget.max_iterations

        # 4. Phase: Extrinsic Validation
        full_report = validate_autoresearch_plan(plan, project_root, phase="all")
        if not full_report.valid:
            self.log_event(
                "extrinsic",
                "validate_extrinsic",
                "error" if fail_on_extrinsic else "warn",
                f"Extrinsic phase validation failed with {full_report.summary.get('errors', 0)} errors",
            )
        else:
            self.log_event("extrinsic", "validate_extrinsic", "ok", "Extrinsic phase contracts passed")
        if not full_report.valid and fail_on_extrinsic:
            return OrchestrationResult(
                project_name=self.project_name,
                success=False,
                phase_reached="extrinsic",
                candidates_processed=0,
                candidate_budget=candidate_budget,
                events=list(self.events),
                report=full_report,
                plan=plan,
            )

        # 5. Write reports if requested
        reports_written = False
        if write_reports:
            try:
                write_autoresearch_report(project_root, full_report)
                reports_written = True
                self.log_event("finalization", "write_reports", "ok", "Wrote AutoResearch report artifacts")
            except OSError as exc:
                self.log_event("finalization", "write_reports", "error", f"Could not write reports: {exc}")
                return OrchestrationResult(
                    project_name=self.project_name,
                    success=False,
                    phase_reached="finalization",
                    candidates_processed=0,
                    candidate_budget=candidate_budget,
                    reports_written=False,
                    events=list(self.events),
                    report=full_report,
                    plan=plan,
                )

        self.log_event(
            "completion",
            "execute_plan",
            "ok" if full_report.valid else "warn",
            "AutoResearch readiness orchestration completed; no candidates were executed",
        )
        return OrchestrationResult(
            project_name=self.project_name,
            success=full_report.valid,
            phase_reached="completed",
            candidates_processed=0,
            candidate_budget=candidate_budget,
            reports_written=reports_written,
            events=list(self.events),
            report=full_report,
            plan=plan,
        )


__all__ = [
    "AutoResearchOrchestrator",
    "OrchestrationEvent",
    "OrchestrationResult",
]
