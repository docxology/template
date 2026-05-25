"""Public dataclasses for deterministic AutoResearch readiness checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_QUALITY_CHECKS = (
    "domain_profile",
    "experiment_plan",
    "pipeline_contracts",
    "evidence_registry",
    "artifact_manifest",
    "thin_orchestrators",
)

KNOWN_QUALITY_CHECKS = frozenset(DEFAULT_QUALITY_CHECKS)


@dataclass(frozen=True)
class AutoResearchConfig:
    """Optional project-local AutoResearch readiness configuration."""

    enabled: bool = True
    strict: bool = False
    topic: str = ""
    quality_checks: tuple[str, ...] = DEFAULT_QUALITY_CHECKS
    stage_gates: tuple[str, ...] = ()
    required_artifacts: tuple[str, ...] = ()
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe payload."""
        payload = asdict(self)
        payload["quality_checks"] = list(self.quality_checks)
        payload["stage_gates"] = list(self.stage_gates)
        payload["required_artifacts"] = list(self.required_artifacts)
        return payload


@dataclass(frozen=True)
class AutoResearchStage:
    """Pipeline stage metadata used by the readiness plan."""

    name: str
    depends_on: tuple[str, ...] = ()
    gate: str | None = None
    input_artifacts: tuple[str, ...] = ()
    output_artifacts: tuple[str, ...] = ()
    definition_of_done: str = ""
    failure_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe payload."""
        return {
            "name": self.name,
            "depends_on": list(self.depends_on),
            "gate": self.gate,
            "input_artifacts": list(self.input_artifacts),
            "output_artifacts": list(self.output_artifacts),
            "definition_of_done": self.definition_of_done,
            "failure_code": self.failure_code,
        }


@dataclass(frozen=True)
class AutoResearchPlan:
    """Deterministic plan assembled from existing project and pipeline metadata."""

    repo_root: Path
    project_root: Path
    project_name: str
    config: AutoResearchConfig
    domain: str = "generic"
    display_name: str = "Generic Research Project"
    experiment_protocol: str = ""
    experiment_conditions: tuple[str, ...] = ()
    stages: tuple[AutoResearchStage, ...] = ()
    declared_gates: tuple[str, ...] = ()
    stage_gates: tuple[str, ...] = ()
    required_artifacts: tuple[str, ...] = ()
    quality_checks: tuple[str, ...] = DEFAULT_QUALITY_CHECKS

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe payload."""
        return {
            "repo_root": str(self.repo_root),
            "project_root": str(self.project_root),
            "project_name": self.project_name,
            "config": self.config.to_dict(),
            "domain": self.domain,
            "display_name": self.display_name,
            "experiment_protocol": self.experiment_protocol,
            "experiment_conditions": list(self.experiment_conditions),
            "stages": [stage.to_dict() for stage in self.stages],
            "declared_gates": list(self.declared_gates),
            "stage_gates": list(self.stage_gates),
            "required_artifacts": list(self.required_artifacts),
            "quality_checks": list(self.quality_checks),
        }


@dataclass(frozen=True)
class AutoResearchIssue:
    """One structured AutoResearch readiness issue."""

    severity: str
    code: str
    message: str
    source_path: str = ""
    suggested_action: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe payload."""
        return asdict(self)


@dataclass(frozen=True)
class AutoResearchReport:
    """Structured AutoResearch readiness validation result."""

    project_name: str
    valid: bool
    issues: tuple[AutoResearchIssue, ...] = ()
    plan: AutoResearchPlan | None = None

    @property
    def summary(self) -> dict[str, int | bool]:
        """Return issue counts and validity flags."""
        errors = sum(1 for issue in self.issues if issue.severity == "error")
        warnings = sum(1 for issue in self.issues if issue.severity == "warning")
        return {
            "valid": self.valid,
            "issues": len(self.issues),
            "errors": errors,
            "warnings": warnings,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe payload."""
        return {
            "project_name": self.project_name,
            "valid": self.valid,
            "summary": self.summary,
            "issues": [issue.to_dict() for issue in self.issues],
            "plan": self.plan.to_dict() if self.plan else None,
        }
