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

METHOD_QUALITY_CHECKS = (
    "method_contracts",
    "review_gates",
    "benchmark_tasks",
    "ai_disclosure",
    "security_profile",
)

KNOWN_QUALITY_CHECKS = frozenset((*DEFAULT_QUALITY_CHECKS, *METHOD_QUALITY_CHECKS))


@dataclass(frozen=True)
class BudgetPolicy:
    """Bounded AutoResearch budget contract."""

    max_iterations: int = 1
    max_wall_clock_minutes: int = 30
    max_llm_calls: int = 0
    max_cost_usd: float = 0.0

    def to_dict(self) -> dict[str, int | float]:
        """Serialize to a JSON-safe payload."""
        return {
            "max_iterations": self.max_iterations,
            "max_wall_clock_minutes": self.max_wall_clock_minutes,
            "max_llm_calls": self.max_llm_calls,
            "max_cost_usd": self.max_cost_usd,
        }


@dataclass(frozen=True)
class ReviewGate:
    """One human review gate in the AutoResearch workflow."""

    name: str
    required: bool = True
    decision: str = ""

    def to_dict(self) -> dict[str, str | bool]:
        """Serialize to a JSON-safe payload."""
        return {
            "name": self.name,
            "required": self.required,
            "decision": self.decision,
        }


@dataclass(frozen=True)
class BenchmarkTask:
    """One benchmark-style grading task declaration."""

    identifier: str
    description: str
    grading_output: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe payload."""
        return {
            "id": self.identifier,
            "description": self.description,
            "grading_output": self.grading_output,
        }


@dataclass(frozen=True)
class EvidenceLink:
    """One claim-to-evidence edge."""

    claim_id: str
    evidence_path: str
    evidence_type: str = "artifact"

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe payload."""
        return {
            "claim_id": self.claim_id,
            "evidence_path": self.evidence_path,
            "evidence_type": self.evidence_type,
        }


@dataclass(frozen=True)
class ResearchIdea:
    """One proposed research idea in a bounded campaign."""

    identifier: str
    title: str
    rationale: str
    status: str
    evidence_links: tuple[EvidenceLink, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe payload."""
        return {
            "id": self.identifier,
            "title": self.title,
            "rationale": self.rationale,
            "status": self.status,
            "evidence_links": [link.to_dict() for link in self.evidence_links],
        }


@dataclass(frozen=True)
class ExperimentCandidate:
    """One experiment candidate proposed by the campaign."""

    identifier: str
    idea_id: str
    status: str
    metric_name: str = ""
    metric_direction: str = "maximize"
    touched_paths: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe payload."""
        return {
            "id": self.identifier,
            "idea_id": self.idea_id,
            "status": self.status,
            "metric_name": self.metric_name,
            "metric_direction": self.metric_direction,
            "touched_paths": list(self.touched_paths),
            "expected_artifacts": list(self.expected_artifacts),
        }


@dataclass(frozen=True)
class ResearchProgram:
    """Human-authored research-program prompt and controls."""

    path: str
    summary: str
    autonomy_level: str
    budget_policy: BudgetPolicy
    edit_allowlist: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe payload."""
        return {
            "path": self.path,
            "summary": self.summary,
            "autonomy_level": self.autonomy_level,
            "budget_policy": self.budget_policy.to_dict(),
            "edit_allowlist": list(self.edit_allowlist),
        }


@dataclass(frozen=True)
class RunLedger:
    """Budget and replay ledger for a bounded AutoResearch run."""

    budget_policy: BudgetPolicy
    iterations_used: int = 0
    wall_clock_minutes_used: int = 0
    llm_calls_used: int = 0
    cost_usd_used: float = 0.0
    budget_exhausted: bool = False
    exhaustion_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe payload."""
        return {
            "budget_policy": self.budget_policy.to_dict(),
            "iterations_used": self.iterations_used,
            "wall_clock_minutes_used": self.wall_clock_minutes_used,
            "llm_calls_used": self.llm_calls_used,
            "cost_usd_used": self.cost_usd_used,
            "budget_exhausted": self.budget_exhausted,
            "exhaustion_reason": self.exhaustion_reason,
        }


@dataclass(frozen=True)
class SecurityProfile:
    """Local security posture declared for deterministic AutoResearch artifacts."""

    enabled: bool = False
    mode: str = "local_deterministic"
    threat_model_frameworks: tuple[str, ...] = ()
    integrity_algorithm: str = "sha256"
    network_policy: str = "default_offline"
    external_signing: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe payload."""
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "threat_model_frameworks": list(self.threat_model_frameworks),
            "integrity_algorithm": self.integrity_algorithm,
            "network_policy": self.network_policy,
            "external_signing": self.external_signing,
        }


@dataclass(frozen=True)
class AutoResearchConfig:
    """Optional project-local AutoResearch readiness configuration."""

    enabled: bool = True
    strict: bool = False
    topic: str = ""
    autonomy_level: str = "proposal_only"
    budget_policy: BudgetPolicy = BudgetPolicy()
    edit_allowlist: tuple[str, ...] = ()
    metric_direction: str = "maximize"
    acceptance_policy: str = ""
    review_gates: tuple[ReviewGate, ...] = ()
    source_manifests: tuple[str, ...] = ()
    benchmark_tasks: tuple[BenchmarkTask, ...] = ()
    disclosure_required: bool = False
    disclosure_text: str = "AI-assisted AutoResearch"
    security_profile: SecurityProfile = SecurityProfile()
    quality_checks: tuple[str, ...] = DEFAULT_QUALITY_CHECKS
    stage_gates: tuple[str, ...] = ()
    required_artifacts: tuple[str, ...] = ()
    source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe payload."""
        payload = asdict(self)
        payload["budget_policy"] = self.budget_policy.to_dict()
        payload["review_gates"] = [gate.to_dict() for gate in self.review_gates]
        payload["benchmark_tasks"] = [task.to_dict() for task in self.benchmark_tasks]
        payload["security_profile"] = self.security_profile.to_dict()
        payload["edit_allowlist"] = list(self.edit_allowlist)
        payload["source_manifests"] = list(self.source_manifests)
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
