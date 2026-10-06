"""Typed fail-closed sections for local release readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from infrastructure.reporting.readiness_receipts import ReadinessEvidence
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES


@dataclass(frozen=True)
class ReleaseMetadata:
    """Version and tag facts read from local files only."""

    version: str | None = None
    latest_tag: str | None = None
    latest_changelog_version: str | None = None
    source: str | None = None

    @property
    def ready(self) -> bool:
        """Require a coherent intended version and local release heading."""
        return bool(self.version and self.latest_changelog_version == self.version)


@dataclass(frozen=True)
class ProjectCoverage:
    """A single project's collected-test and coverage facts."""

    name: str
    tests: int | None
    coverage_percent: float | None


@dataclass(frozen=True)
class CoverageFacts:
    """Coverage/test facts parsed from COUNTS.md."""

    available: bool = False
    projects: list[ProjectCoverage] = field(default_factory=list)
    source: str | None = None

    @property
    def ready(self) -> bool:
        """Require nonempty measured tests and the project coverage floor."""
        return (
            self.available
            and {p.name for p in self.projects} == {name.split("/")[-1] for name in PUBLIC_PROJECT_NAMES}
            and len(self.projects) == len(PUBLIC_PROJECT_NAMES)
            and all(
                p.tests is not None
                and p.tests > 0
                and p.coverage_percent is not None
                and 90 <= p.coverage_percent <= 100
                for p in self.projects
            )
        )


@dataclass(frozen=True)
class PipelineState:
    """Newest pipeline-report snapshot, if any."""

    available: bool = False
    source: str | None = None
    total_stages: int = 0
    passed_stages: int = 0
    failed_stages: int = 0
    total_duration: float | None = None
    validated: bool = False

    @property
    def ready(self) -> bool:
        """Return True if the artifact is ready for publication."""
        return (
            self.available
            and self.validated
            and self.failed_stages == 0
            and self.total_stages > 0
            and self.passed_stages == self.total_stages
        )


@dataclass(frozen=True)
class EvidenceGraphStatus:
    """Evidence-graph generation status."""

    available: bool = False
    source: str | None = None
    node_count: int | None = None
    edge_count: int | None = None

    @property
    def ready(self) -> bool:
        """Require a populated graph and a valid edge collection."""
        return self.available and self.node_count is not None and self.node_count > 0 and self.edge_count is not None


@dataclass(frozen=True)
class DocsLintStatus:
    """Documentation-lint status from a JSON snapshot."""

    available: bool = False
    source: str | None = None
    mermaid: int = 0
    broken_links: int = 0
    consistency: int = 0
    doc_pairs: int = 0
    valid: bool = False

    @property
    def total_issues(self) -> int:
        """Return the total number of issues across all categories."""
        return self.mermaid + self.broken_links + self.consistency + self.doc_pairs

    @property
    def ready(self) -> bool:
        """Return True if the artifact is ready for publication."""
        return self.available and self.valid and self.total_issues == 0


@dataclass(frozen=True)
class ReleaseReadinessReport:
    """Consolidated, typed release-readiness view."""

    generated_at: str
    release: ReleaseMetadata
    coverage: CoverageFacts
    pipeline: PipelineState
    evidence_graph: EvidenceGraphStatus
    docs_lint: DocsLintStatus
    evidence: ReadinessEvidence = field(default_factory=ReadinessEvidence)

    @property
    def overall_ready(self) -> bool:
        """Require full published acceptance for every source-owned obligation."""
        return self.evidence.released_state == "pass" and self.evidence.current

    @property
    def candidate_ready(self) -> bool:
        """Allow preparation only after complete candidate acceptance."""
        return self.evidence.candidate_state == "pass"

    @property
    def status(self) -> str:
        """Expose explicit pass/fail/blocked/unknown released acceptance."""
        return self.evidence.released_state

    def to_dict(self) -> dict[str, Any]:
        """Return a plain, JSON-serializable dict (byte-stable with sort_keys)."""
        return {
            "generated_at": self.generated_at,
            "overall_ready": self.overall_ready,
            "candidate_ready": self.candidate_ready,
            "candidate_status": self.evidence.candidate_state,
            "released_status": self.evidence.released_state,
            "preparation_allowed": self.candidate_ready,
            "production_authorized": False,
            "status": self.status,
            "evidence": self.evidence.to_dict(),
            "release": asdict(self.release),
            "coverage": {
                "available": self.coverage.available,
                "source": self.coverage.source,
                "projects": [asdict(p) for p in self.coverage.projects],
            },
            "pipeline": {**asdict(self.pipeline), "ready": self.pipeline.ready},
            "evidence_graph": asdict(self.evidence_graph),
            "docs_lint": {
                **asdict(self.docs_lint),
                "total_issues": self.docs_lint.total_issues,
                "ready": self.docs_lint.ready,
            },
        }
