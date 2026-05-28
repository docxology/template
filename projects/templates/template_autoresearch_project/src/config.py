"""Configuration helpers for the deterministic AutoResearch exemplar."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from infrastructure.autoresearch import (
    AutoResearchPlan,
    BenchmarkTask,
    BudgetPolicy,
    EvidenceLink,
    ExperimentCandidate,
    ResearchIdea,
    ReviewGate,
    SecurityProfile,
    parse_string_sequence,
)

HUMAN_REVIEW_SCHEMA = "template-autoresearch-human-review-v1"
HUMAN_REVIEW_DECISIONS = frozenset({"approved", "deferred", "rejected"})


@dataclass(frozen=True)
class ResearchQuestion:
    """One configured research question for the loop."""

    identifier: str
    question: str
    expected_evidence: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe mapping."""
        return {
            "identifier": self.identifier,
            "question": self.question,
            "expected_evidence": self.expected_evidence,
        }


@dataclass(frozen=True)
class ManuscriptLoopSettings:
    """Manuscript-only loop settings from config.yaml."""

    review_policy: str
    research_questions: tuple[ResearchQuestion, ...]
    loop_stages: tuple[str, ...]


@dataclass(frozen=True)
class HumanReviewState:
    """Human-authored publication review state loaded from human_review.yaml."""

    schema: str = HUMAN_REVIEW_SCHEMA
    publication_approved: bool = False
    reviewer: str = ""
    reviewed_at: str | None = None
    decisions: dict[str, str] = field(
        default_factory=lambda: {
            "proposal_review": "deferred",
            "evidence_review": "deferred",
        }
    )
    notes: str = ""
    source_path: str = "human_review.yaml"
    source_exists: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
            "schema": self.schema,
            "publication_approved": self.publication_approved,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "decisions": dict(self.decisions),
            "notes": self.notes,
            "source_path": self.source_path,
            "source_exists": self.source_exists,
        }


@dataclass(frozen=True)
class AutoResearchLoopConfig:
    """Project-local deterministic AutoResearch loop configuration."""

    topic: str
    review_policy: str
    research_questions: tuple[ResearchQuestion, ...]
    loop_stages: tuple[str, ...]
    required_artifacts: tuple[str, ...]
    quality_checks: tuple[str, ...]
    autonomy_level: str = "proposal_only"
    budget_policy: BudgetPolicy = BudgetPolicy()
    edit_allowlist: tuple[str, ...] = ()
    acceptance_policy: str = ""
    disclosure_text: str = "AI-assisted AutoResearch"
    review_gates: tuple[ReviewGate, ...] = ()
    benchmark_tasks: tuple[BenchmarkTask, ...] = ()
    security_profile: SecurityProfile = SecurityProfile()
    human_review: HumanReviewState = HumanReviewState()

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
            "topic": self.topic,
            "autonomy_level": self.autonomy_level,
            "review_policy": self.review_policy,
            "research_questions": [question.to_dict() for question in self.research_questions],
            "loop_stages": list(self.loop_stages),
            "required_artifacts": list(self.required_artifacts),
            "quality_checks": list(self.quality_checks),
            "budget_policy": self.budget_policy.to_dict(),
            "edit_allowlist": list(self.edit_allowlist),
            "acceptance_policy": self.acceptance_policy,
            "disclosure_text": self.disclosure_text,
            "review_gates": [gate.to_dict() for gate in self.review_gates],
            "benchmark_tasks": [task.to_dict() for task in self.benchmark_tasks],
            "security_profile": self.security_profile.to_dict(),
            "human_review": self.human_review.to_dict(),
        }


def load_manuscript_loop_settings(project_root: Path) -> ManuscriptLoopSettings:
    """Load loop stage and question settings from manuscript config."""
    manuscript_config = _load_yaml(project_root / "manuscript" / "config.yaml")
    project_config = manuscript_config.get("project_config", {})
    if not isinstance(project_config, dict):
        raise ValueError("manuscript/config.yaml project_config must be a mapping")

    questions = _parse_questions(project_config.get("research_questions", []))
    loop_stages = parse_string_sequence(
        project_config.get("loop_stages"),
        default=("plan", "gate", "evidence", "claims", "artifacts", "readiness"),
    )
    return ManuscriptLoopSettings(
        review_policy=str(project_config.get("review_policy", "human_review_required")),
        research_questions=questions,
        loop_stages=loop_stages,
    )


def load_human_review(path: Path) -> HumanReviewState:
    """Load the human-authored publication review state."""
    if not path.is_file():
        return HumanReviewState(source_path=path.name, source_exists=False)
    payload = _load_yaml(path)
    schema = str(payload.get("schema", "") or "")
    if schema != HUMAN_REVIEW_SCHEMA:
        raise ValueError(f"human_review.yaml schema must be {HUMAN_REVIEW_SCHEMA}")
    publication_approved = payload.get("publication_approved")
    if not isinstance(publication_approved, bool):
        raise ValueError("human_review.yaml publication_approved must be a boolean")
    reviewer = str(payload.get("reviewer", "") or "").strip()
    reviewed_at_raw = payload.get("reviewed_at")
    reviewed_at = None if reviewed_at_raw is None else str(reviewed_at_raw).strip()
    if not publication_approved and reviewed_at:
        raise ValueError("human_review.yaml reviewed_at must be null unless publication_approved is true")
    if publication_approved and (not reviewer or not reviewed_at):
        raise ValueError("human_review.yaml approvals require reviewer and reviewed_at")
    raw_decisions = payload.get("decisions", {})
    if not isinstance(raw_decisions, dict):
        raise ValueError("human_review.yaml decisions must be a mapping")
    decisions: dict[str, str] = {}
    for gate, decision in raw_decisions.items():
        gate_name = str(gate).strip()
        decision_text = str(decision).strip()
        if decision_text not in HUMAN_REVIEW_DECISIONS:
            allowed = ", ".join(sorted(HUMAN_REVIEW_DECISIONS))
            raise ValueError(f"human_review.yaml decision for {gate_name} must be one of: {allowed}")
        decisions[gate_name] = decision_text
    return HumanReviewState(
        publication_approved=publication_approved,
        reviewer=reviewer,
        reviewed_at=reviewed_at,
        decisions=decisions or HumanReviewState().decisions,
        notes=str(payload.get("notes", "") or ""),
        source_path=path.name,
        source_exists=True,
    )


def build_loop_config(
    plan: AutoResearchPlan,
    settings: ManuscriptLoopSettings,
    *,
    human_review: HumanReviewState | None = None,
) -> AutoResearchLoopConfig:
    """Merge plan metadata with manuscript loop settings."""
    return AutoResearchLoopConfig(
        topic=plan.config.topic,
        autonomy_level=plan.config.autonomy_level,
        review_policy=settings.review_policy,
        research_questions=settings.research_questions,
        loop_stages=settings.loop_stages,
        required_artifacts=plan.required_artifacts,
        quality_checks=plan.quality_checks,
        budget_policy=plan.config.budget_policy,
        edit_allowlist=plan.config.edit_allowlist,
        acceptance_policy=plan.config.acceptance_policy,
        disclosure_text=plan.config.disclosure_text,
        review_gates=plan.config.review_gates,
        benchmark_tasks=plan.config.benchmark_tasks,
        security_profile=plan.config.security_profile,
        human_review=human_review or HumanReviewState(),
    )


def load_loop_config(project_root: Path, plan: AutoResearchPlan | None = None) -> AutoResearchLoopConfig:
    """Load loop configuration, optionally merged with a composed plan."""
    settings = load_manuscript_loop_settings(project_root)
    if plan is None:
        from infrastructure.autoresearch import build_autoresearch_plan

        repo_root = project_root.parents[1]
        plan = build_autoresearch_plan(repo_root, project_root.name)
    return build_loop_config(plan, settings, human_review=load_human_review(project_root / "human_review.yaml"))


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return payload


def _parse_questions(raw: Any) -> tuple[ResearchQuestion, ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("project_config.research_questions must be a non-empty list")
    questions: list[ResearchQuestion] = []
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, dict):
            raise ValueError("research question entries must be mappings")
        identifier = str(row.get("id") or f"rq{index}")
        question = str(row.get("question") or "").strip()
        expected_evidence = str(row.get("expected_evidence") or "").strip()
        if not question or not expected_evidence:
            raise ValueError(f"research question {identifier} must declare question and expected_evidence")
        questions.append(
            ResearchQuestion(
                identifier=identifier,
                question=question,
                expected_evidence=expected_evidence,
            )
        )
    return tuple(questions)


def load_seed_ideas(project_root: Path) -> tuple[ResearchIdea, ...]:
    """Load file-backed seed ideas for the bounded exemplar campaign."""
    payload = _load_yaml(project_root / "seed_ideas.yaml")
    raw_ideas = payload.get("ideas", [])
    if not isinstance(raw_ideas, list):
        raise ValueError("seed_ideas.yaml ideas must be a list")
    ideas: list[ResearchIdea] = []
    for row in raw_ideas:
        if not isinstance(row, dict):
            raise ValueError("seed idea entries must be mappings")
        identifier = str(row.get("id", "") or "").strip()
        title = str(row.get("title", "") or "").strip()
        rationale = str(row.get("rationale", "") or "").strip()
        status = str(row.get("status", "") or "").strip()
        if not identifier or not title or not rationale or not status:
            raise ValueError("seed ideas must declare id, title, rationale, and status")
        ideas.append(
            ResearchIdea(
                identifier=identifier,
                title=title,
                rationale=rationale,
                status=status,
                evidence_links=_parse_evidence_links(row.get("evidence_links", []), default_claim_id=identifier),
            )
        )
    return tuple(ideas)


def load_experiment_candidates(project_root: Path) -> tuple[ExperimentCandidate, ...]:
    """Load candidate experiments nested under seed ideas."""
    payload = _load_yaml(project_root / "seed_ideas.yaml")
    raw_ideas = payload.get("ideas", [])
    if not isinstance(raw_ideas, list):
        return ()
    candidates: list[ExperimentCandidate] = []
    for idea in raw_ideas:
        if not isinstance(idea, dict):
            continue
        idea_id = str(idea.get("id", "") or "")
        raw_candidates = idea.get("candidates", [])
        if not isinstance(raw_candidates, list):
            continue
        for row in raw_candidates:
            if not isinstance(row, dict):
                continue
            candidates.append(
                ExperimentCandidate(
                    identifier=str(row.get("id", "") or ""),
                    idea_id=idea_id,
                    status=str(row.get("status", "") or ""),
                    metric_name=str(row.get("metric_name", "") or ""),
                    metric_direction=str(row.get("metric_direction", "maximize") or "maximize"),
                    touched_paths=parse_string_sequence(row.get("touched_paths"), default=()),
                    expected_artifacts=parse_string_sequence(row.get("expected_artifacts"), default=()),
                )
            )
    return tuple(candidate for candidate in candidates if candidate.identifier)


def _parse_evidence_links(raw: Any, *, default_claim_id: str) -> tuple[EvidenceLink, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError("evidence_links must be a list")
    links: list[EvidenceLink] = []
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("evidence link entries must be mappings")
        evidence_path = str(row.get("evidence_path", "") or "").strip()
        if not evidence_path:
            continue
        links.append(
            EvidenceLink(
                claim_id=str(row.get("claim_id", default_claim_id) or default_claim_id),
                evidence_path=evidence_path,
                evidence_type=str(row.get("evidence_type", "artifact") or "artifact"),
            )
        )
    return tuple(links)
