#!/usr/bin/env python3
"""Negative controls for pipeline single-source-of-truth boundaries."""

from __future__ import annotations

import subprocess
from pathlib import Path
from zipfile import ZipFile

from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor


def test_built_wheel_contains_canonical_pipeline_yaml(tmp_path: Path) -> None:
    """Installed-wheel fallback data must exist, not merely work in a checkout."""
    repo_root = Path(__file__).parents[4]
    dist = tmp_path / "dist"
    result = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    wheel = next(dist.glob("*.whl"))
    with ZipFile(wheel) as archive:
        assert "infrastructure/core/pipeline/pipeline.yaml" in archive.namelist()


def test_missing_repository_yaml_uses_packaged_canonical_dag(tmp_path: Path) -> None:
    """A minimal checkout cannot silently select a second Python stage list."""
    repo_root = tmp_path / "minimal-fork"
    (repo_root / "projects" / "p" / "output").mkdir(parents=True)
    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))

    resolved = executor._resolve_pipeline_yaml()
    assert resolved == Path(__file__).parents[4] / "infrastructure/core/pipeline/pipeline.yaml"

    expected = PipelineDAG.from_yaml(resolved)
    expected.filter_tags(exclude={"llm", "ebook", "metadata", "bundle", "archival", "science", "provenance"})
    expected_names = [stage.name for stage in expected.sorted_stages()]
    actual_names = [stage.name for stage in executor._build_stage_list(include_llm=False, skip_clean=False)]
    assert actual_names == expected_names


def test_missing_canonical_stage_does_not_run_unrelated_root_copy(tmp_path: Path) -> None:
    """An unrelated root implementation cannot mask a missing canonical stage."""
    repo_root = tmp_path / "minimal-fork"
    project_dir = repo_root / "projects" / "p" / "output"
    project_dir.mkdir(parents=True)
    unrelated = repo_root / "scripts" / "02_run_analysis.py"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("raise SystemExit(0)\n", encoding="utf-8")

    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    assert executor._run_script("scripts/pipeline/stage_02_analysis.py", "--project", "p") is False


def test_canonical_entrypoints_export_their_own_implementations() -> None:
    """Canonical entrypoints expose the implementation used by the pipeline."""
    from scripts.pipeline.stage_06_llm_review import cli_main as canonical_llm_cli
    from scripts.pipeline.stage_07_executive_report import main as canonical_report_main
    from scripts.runner import execute_pipeline as canonical_pipeline

    assert callable(canonical_pipeline.execute_pipeline)
    assert callable(canonical_pipeline.execute_single_stage)
    assert callable(canonical_pipeline.handle_hitl_command)
    assert callable(canonical_pipeline.main)
    assert callable(canonical_llm_cli)
    assert callable(canonical_report_main)


def test_removed_root_entrypoints_are_absent() -> None:
    """There is one repository-wide path for each migrated entrypoint."""
    repo_root = Path(__file__).parents[4]
    removed = (
        "scripts/01_run_tests.py",
        "scripts/02_run_analysis.py",
        "scripts/06_llm_review.py",
        "scripts/08_connector_search.py",
        "scripts/09_provenance_record.py",
        "scripts/10_research_workflow.py",
        "scripts/execute_pipeline.py",
        "scripts/run_matrix.py",
    )
    assert all(not (repo_root / relative).exists() for relative in removed)


def test_canonical_entrypoints_remain_directly_executable() -> None:
    """Canonical entrypoints remain directly executable after consolidation."""
    repo_root = Path(__file__).parents[4]
    for relative in (
        "scripts/runner/execute_pipeline.py",
        "scripts/pipeline/stage_06_llm_review.py",
        "scripts/pipeline/stage_07_executive_report.py",
    ):
        script = repo_root / relative
        assert script.stat().st_mode & 0o111, f"{relative} lost its executable bit"
        result = subprocess.run(
            [str(script), "--help"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"{relative}: {result.stderr}"
        assert "usage:" in result.stdout.lower()
