"""Tests for the template benchmark harness."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.benchmark.template_harness import (
    BenchmarkManifest,
    write_default_manifest,
    load_benchmark_manifest,
    score_project_against_manifest,
    scores_to_markdown,
)
from infrastructure.benchmark.rubrics import RubricSet, score_rubric


def _write_project_outputs(project: Path) -> None:
    (project / "output" / "pdf").mkdir(parents=True)
    (project / "output" / "reports").mkdir(parents=True)
    (project / "output" / "data").mkdir(parents=True)
    (project / "output" / "figures").mkdir(parents=True)
    (project / "manuscript").mkdir()
    (project / "output" / "pdf" / "paper.pdf").write_bytes(b"%PDF-1.4")
    (project / "output" / "reports" / "validation_report.json").write_text(
        '{"overall_status": "pass"}',
        encoding="utf-8",
    )
    (project / "output" / "data" / "manuscript_variables.json").write_text(
        '{"CLAIMED_VALUE": 12}',
        encoding="utf-8",
    )
    (project / "output" / "figures" / "plot.png").write_bytes(b"png")
    (project / "output" / "reports" / "artifact_manifest.json").write_text(
        '{"entries": [{"path": "output/pdf/paper.pdf"}], "issues": []}',
        encoding="utf-8",
    )
    (project / "manuscript" / "paper.md").write_text(
        "The claimed value is 12. See @smith2026 and Figure @fig:plot.\n",
        encoding="utf-8",
    )
    (project / "manuscript" / "references.bib").write_text(
        "@article{smith2026,title={A}}\n",
        encoding="utf-8",
    )


def test_load_benchmark_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "name": "template-smoke",
                "projects": ["template_code_project", "template_prose_project"],
                "required_outputs": ["output/pdf", "output/reports/validation_report.json"],
                "checks": [
                    "output_validity",
                    "evidence_grounding",
                    "reproducibility_bundle",
                    "artifact_manifest",
                ],
                "rubric": {
                    "name": "template-quality",
                    "dimensions": [
                        {"name": "output_validity", "weight": 1.0},
                        {"name": "evidence_grounding", "weight": 2.0},
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = load_benchmark_manifest(manifest_path)

    assert manifest.name == "template-smoke"
    assert manifest.projects == ("template_code_project", "template_prose_project")
    assert "evidence_grounding" in manifest.checks
    assert manifest.rubric is not None
    assert manifest.rubric.dimensions[1].weight == 2.0


def test_score_project_against_manifest_passes_grounded_project(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "template_code_project"
    _write_project_outputs(project)
    manifest = BenchmarkManifest(
        name="template-smoke",
        projects=("template_code_project",),
        required_outputs=("output/pdf", "output/reports/validation_report.json"),
        checks=("output_validity", "evidence_grounding", "reproducibility_bundle", "artifact_manifest"),
    )

    score = score_project_against_manifest(project, manifest)

    assert score.project == "template_code_project"
    assert score.passed is True
    assert score.score == 4
    assert score.max_score == 4


def test_score_project_flags_missing_required_output(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "template_prose_project"
    project.mkdir(parents=True)
    manifest = BenchmarkManifest(
        name="template-smoke",
        projects=("template_prose_project",),
        required_outputs=("output/pdf",),
        checks=("output_validity",),
    )

    score = score_project_against_manifest(project, manifest)

    assert score.passed is False
    assert any("missing required output" in issue for issue in score.issues)


def test_rubric_weighted_scoring_and_markdown_output(tmp_path: Path) -> None:
    rubric = RubricSet.from_dict(
        {
            "name": "publication",
            "dimensions": [
                {"name": "rendering", "weight": 1.0},
                {"name": "evidence_grounding", "weight": 3.0},
            ],
        }
    )

    result = score_rubric({"rendering": True, "evidence_grounding": False}, rubric)
    markdown = scores_to_markdown(
        [
            score_project_against_manifest(
                tmp_path / "missing",
                BenchmarkManifest(
                    name="template-smoke",
                    projects=("missing",),
                    required_outputs=("output/pdf",),
                    checks=("output_validity",),
                ),
            )
        ]
    )

    assert result.score == 1.0
    assert result.max_score == 4.0
    assert "template-smoke" not in markdown
    assert "| missing |" in markdown


def test_write_default_manifest_uses_canonical_projects_and_profile_rubric(tmp_path: Path) -> None:
    repo_root = tmp_path
    code_project = repo_root / "projects" / "templates" / "template_code_project"
    prose_project = repo_root / "projects" / "templates" / "template_prose_project"
    rotating_project = repo_root / "projects" / "rotating_private"
    code_project.mkdir(parents=True)
    prose_project.mkdir(parents=True)
    rotating_project.mkdir(parents=True)
    (code_project / "domain_profile.yaml").write_text(
        """
domain: code_research
display_name: Code Research
benchmark_rubric:
  name: code-rubric
  dimensions:
    - name: evidence_grounding
      weight: 3.0
""",
        encoding="utf-8",
    )
    manifest_path = repo_root / "manifest.json"

    manifest = write_default_manifest(repo_root=repo_root, output_path=manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest.projects == ("templates/template_code_project", "templates/template_prose_project")
    assert "rotating_private" not in payload["projects"]
    assert manifest.rubric is not None
    assert manifest.rubric.name == "code-rubric"
    assert manifest.rubric.dimensions[0].weight == 3.0
