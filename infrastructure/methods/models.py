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

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
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

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
            "project_name": self.project_name,
            "project_root": self.project_root.as_posix(),
            "pipeline_source": self.pipeline_source.as_posix(),
            "method_sections": list(self.method_sections),
            "artifact_manifest": self.artifact_manifest.as_posix(),
            "evidence_registry": self.evidence_registry.as_posix(),
            "stages": [stage.to_dict() for stage in self.stages],
            "validation_commands": list(self.validation_commands),
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
