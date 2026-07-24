"""Dataclasses for project methods orchestration plans."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MethodStage:
    """One pipeline stage viewed as a methods/reproducibility contract."""

    name: str
    order: int
    depends_on: tuple[str, ...]
    tags: tuple[str, ...]
    gate: str
    script: str
    method: str
    input_artifacts: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    definition_of_done: str
    failure_code: str
    verification_commands: tuple[str, ...]
    key: str = ""
    executor_method: str = ""
    allow_skip: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
            "key": self.key,
            "name": self.name,
            "order": self.order,
            "depends_on": list(self.depends_on),
            "tags": list(self.tags),
            "gate": self.gate,
            "script": self.script,
            "method": self.method,
            "input_artifacts": list(self.input_artifacts),
            "output_artifacts": list(self.output_artifacts),
            "definition_of_done": self.definition_of_done,
            "failure_code": self.failure_code,
            "verification_commands": list(self.verification_commands),
            "executor_method": self.executor_method,
            "allow_skip": self.allow_skip,
        }


@dataclass(frozen=True)
class MethodsOrchestrationPlan:
    """Repository-derived methods orchestration plan for one project."""

    project_name: str
    project_root: Path
    pipeline_source: Path
    method_sections: tuple[str, ...]
    artifact_manifest: Path
    evidence_registry: Path
    stages: tuple[MethodStage, ...]
    validation_commands: tuple[str, ...]
    dropped_dependency_edges: tuple[tuple[str, str], ...] = ()
    schema_version: str = "1.0"
    artifact_mode: str = "rendered"
    figure_registry: Path | None = None
    claim_ledger: Path | None = None
    experiment_plan: Path | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
            "schema_version": self.schema_version,
            "artifact_mode": self.artifact_mode,
            "project_name": self.project_name,
            "project_root": self.project_root.as_posix(),
            "pipeline_source": self.pipeline_source.as_posix(),
            "method_sections": list(self.method_sections),
            "artifact_manifest": self.artifact_manifest.as_posix(),
            "evidence_registry": self.evidence_registry.as_posix(),
            "figure_registry": self.figure_registry.as_posix() if self.figure_registry else None,
            "claim_ledger": self.claim_ledger.as_posix() if self.claim_ledger else None,
            "experiment_plan": self.experiment_plan.as_posix() if self.experiment_plan else None,
            "stages": [stage.to_dict() for stage in self.stages],
            "validation_commands": list(self.validation_commands),
            "dropped_dependency_edges": [list(edge) for edge in self.dropped_dependency_edges],
        }


@dataclass(frozen=True)
class MethodsIssue:
    """One methods orchestration validation issue."""

    severity: str
    code: str
    message: str
    path: str
    suggestion: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe mapping."""
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class MethodsProjectAudit:
    """Methods audit result for one project."""

    plan: MethodsOrchestrationPlan
    issues: tuple[MethodsIssue, ...]

    @property
    def passed(self) -> bool:
        """Return whether the project has no blocking issues."""
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        payload = self.plan.to_dict()
        payload["issues"] = [issue.to_dict() for issue in self.issues]
        payload["passed"] = self.passed
        return payload


@dataclass(frozen=True)
class MethodsAuditReport:
    """Aggregate methods audit across one or more projects."""

    projects: tuple[MethodsProjectAudit, ...]
    artifact_mode: str = "rendered"
    schema_version: str = "1.0"

    @property
    def error_count(self) -> int:
        """Return the number of blocking validation issues."""
        return sum(issue.severity == "error" for project in self.projects for issue in project.issues)

    @property
    def warning_count(self) -> int:
        """Return the number of non-blocking warnings."""
        return sum(issue.severity == "warning" for project in self.projects for issue in project.issues)

    @property
    def passed(self) -> bool:
        """Return whether every audited project passed."""
        return self.error_count == 0

    def to_dict(self) -> dict[str, object]:
        """Serialize the complete audit without dropping plan fields."""
        return {
            "schema_version": self.schema_version,
            "artifact_mode": self.artifact_mode,
            "passed": self.passed,
            "project_count": len(self.projects),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "projects": [project.to_dict() for project in self.projects],
        }
