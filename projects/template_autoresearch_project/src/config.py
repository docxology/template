"""Configuration helpers for the deterministic AutoResearch exemplar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.autoresearch import AutoResearchPlan, parse_string_sequence


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
class AutoResearchLoopConfig:
    """Project-local deterministic AutoResearch loop configuration."""

    topic: str
    review_policy: str
    research_questions: tuple[ResearchQuestion, ...]
    loop_stages: tuple[str, ...]
    required_artifacts: tuple[str, ...]
    quality_checks: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-safe mapping."""
        return {
            "topic": self.topic,
            "review_policy": self.review_policy,
            "research_questions": [question.to_dict() for question in self.research_questions],
            "loop_stages": list(self.loop_stages),
            "required_artifacts": list(self.required_artifacts),
            "quality_checks": list(self.quality_checks),
        }


def load_manuscript_loop_settings(project_root: Path) -> ManuscriptLoopSettings:
    """Load loop stage and question settings from manuscript config."""
    manuscript_config = _load_yaml(project_root / "manuscript" / "config.yaml")
    project_config = manuscript_config.get("autoresearch_project", {})
    if not isinstance(project_config, dict):
        raise ValueError("manuscript/config.yaml autoresearch_project must be a mapping")

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


def build_loop_config(plan: AutoResearchPlan, settings: ManuscriptLoopSettings) -> AutoResearchLoopConfig:
    """Merge plan metadata with manuscript loop settings."""
    return AutoResearchLoopConfig(
        topic=plan.config.topic,
        review_policy=settings.review_policy,
        research_questions=settings.research_questions,
        loop_stages=settings.loop_stages,
        required_artifacts=plan.required_artifacts,
        quality_checks=plan.quality_checks,
    )


def load_loop_config(project_root: Path, plan: AutoResearchPlan | None = None) -> AutoResearchLoopConfig:
    """Load loop configuration, optionally merged with a composed plan."""
    settings = load_manuscript_loop_settings(project_root)
    if plan is None:
        from infrastructure.autoresearch import build_autoresearch_plan

        repo_root = project_root.parents[1]
        plan = build_autoresearch_plan(repo_root, project_root.name)
    return build_loop_config(plan, settings)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return payload


def _parse_questions(raw: Any) -> tuple[ResearchQuestion, ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("autoresearch_project.research_questions must be a non-empty list")
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
