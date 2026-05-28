"""Tests for project-local domain profile overlays."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.domain_profile import DomainProfile, load_domain_profile
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_load_domain_profile_from_project_yaml(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "domain_profile.yaml").write_text(
        """
domain: computational_biology
display_name: Computational Biology
required_packages: [numpy, scipy]
preferred_outputs: [pdf, html, docx]
validation_gates: [literature_source_quality, publication_readiness]
figure_types: [dose_response, network]
citation_policy: official_or_scholarly
llm_prompt_guidance: "Prefer mechanistic claims with direct evidence."
review_gates: [source_quality]
source_policy: "prefer peer reviewed sources"
artifact_expectations:
  - output/pdf
benchmark_rubric:
  name: computational-biology
  dimensions:
    - name: evidence_grounding
      weight: 2.0
""",
        encoding="utf-8",
    )

    profile = load_domain_profile(project)

    assert profile == DomainProfile(
        domain="computational_biology",
        display_name="Computational Biology",
        required_packages=("numpy", "scipy"),
        preferred_outputs=("pdf", "html", "docx"),
        validation_gates=("literature_source_quality", "publication_readiness"),
        figure_types=("dose_response", "network"),
        citation_policy="official_or_scholarly",
        llm_prompt_guidance="Prefer mechanistic claims with direct evidence.",
        review_gates=("source_quality",),
        source_policy="prefer peer reviewed sources",
        artifact_expectations=("output/pdf",),
        benchmark_rubric={
            "name": "computational-biology",
            "dimensions": [{"name": "evidence_grounding", "weight": 2.0}],
        },
    )


def test_missing_domain_profile_returns_generic_profile(tmp_path: Path) -> None:
    profile = load_domain_profile(tmp_path)

    assert profile.domain == "generic"
    assert profile.display_name == "Generic Research Project"


def test_unknown_domain_profile_key_raises(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "domain_profile.yaml").write_text(
        "domain: x\nnot_a_supported_key: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported domain_profile key"):
        load_domain_profile(project)


def test_builtin_profile_can_be_selected_without_project_file(tmp_path: Path) -> None:
    profile = load_domain_profile(tmp_path, default_profile="literature_review")

    assert profile.domain == "literature_review"
    assert "source_quality" in profile.validation_gates
    assert profile.citation_policy == "official_or_scholarly"


def test_valid_experiment_plan_loads_condition_roles_and_metrics(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "experiment_plan.yaml").write_text(
        """
conditions:
  - name: baseline
    role: reference
  - name: proposed
    role: proposed
  - name: ablation
    role: variant
metrics:
  primary:
    name: accuracy
    direction: maximize
protocol: "Run all conditions with identical seeds."
expected_figures: [fig:accuracy]
expected_tables: [tbl:results]
baselines: [baseline]
ablations: [ablation]
""",
        encoding="utf-8",
    )

    plan = load_experiment_plan(project)
    result = validate_experiment_plan(plan)

    assert plan is not None
    assert result.valid is True
    assert [condition.role for condition in plan.conditions] == ["reference", "proposed", "variant"]
    assert plan.primary_metric.name == "accuracy"
    assert plan.baselines == ("baseline",)
    assert plan.ablations == ("ablation",)


def test_invalid_experiment_plan_reports_missing_primary_metric_and_bad_role(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "experiment_plan.yaml").write_text(
        """
conditions:
  - name: broken
    role: baseline
metrics: {}
protocol: ""
""",
        encoding="utf-8",
    )

    plan = load_experiment_plan(project)
    result = validate_experiment_plan(plan)

    assert plan is not None
    assert result.valid is False
    assert any("invalid condition role" in issue for issue in result.issues)
    assert any("primary metric" in issue for issue in result.issues)
    assert any("baseline" in issue for issue in result.issues)


def test_unknown_experiment_plan_key_raises(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "experiment_plan.yaml").write_text(
        "conditions: []\nunsupported: true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported experiment_plan key"):
        load_experiment_plan(project)


@pytest.mark.parametrize(
    ("project_name", "expected_domain", "expected_primary_metric"),
    [
        ("template_code_project", "code_research", "objective_value"),
        ("template_prose_project", "prose_research", "readability_grade"),
    ],
)
def test_canonical_template_projects_ship_valid_composability_overlays(
    project_name: str,
    expected_domain: str,
    expected_primary_metric: str,
) -> None:
    project_root = REPO_ROOT / "projects" / "templates" / project_name

    profile = load_domain_profile(project_root)
    plan = load_experiment_plan(project_root)
    validation = validate_experiment_plan(plan)

    assert profile.domain == expected_domain
    assert profile.review_gates
    assert profile.artifact_expectations
    assert profile.benchmark_rubric is not None
    assert plan is not None
    assert validation.valid is True, validation.issues
    assert plan.primary_metric is not None
    assert plan.primary_metric.name == expected_primary_metric
    assert plan.baselines
    assert plan.ablations
