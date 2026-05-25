"""Data models for the deterministic AutoResearch loop."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .config import AutoResearchLoopConfig


@dataclass(frozen=True)
class LoopStageResult:
    """One deterministic loop stage result."""

    name: str
    status: str
    evidence: str
    suggested_action: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe mapping."""
        return asdict(self)


@dataclass(frozen=True)
class AutoResearchClaim:
    """One claim generated from local deterministic evidence."""

    identifier: str
    statement: str
    evidence_path: str
    supported: bool

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return asdict(self)


@dataclass(frozen=True)
class AutoResearchLoopResult:
    """Result of one full deterministic AutoResearch loop."""

    project_name: str
    generated_at: str
    config: AutoResearchLoopConfig
    stage_results: tuple[LoopStageResult, ...]
    claims: tuple[AutoResearchClaim, ...]
    readiness_valid: bool
    output_paths: tuple[str, ...]
    ml_task: dict[str, object] = field(default_factory=dict)

    @property
    def supported_claim_count(self) -> int:
        """Return the number of supported generated claims."""
        return sum(1 for claim in self.claims if claim.supported)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe mapping."""
        return {
            "project_name": self.project_name,
            "generated_at": self.generated_at,
            "config": self.config.to_dict(),
            "stage_results": [stage.to_dict() for stage in self.stage_results],
            "claims": [claim.to_dict() for claim in self.claims],
            "metrics": {
                "stage_count": len(self.stage_results),
                "supported_claim_count": self.supported_claim_count,
                "required_artifact_count": len(self.config.required_artifacts),
                "readiness_valid": self.readiness_valid,
            },
            "ml_task": dict(self.ml_task),
            "output_paths": list(self.output_paths),
        }
