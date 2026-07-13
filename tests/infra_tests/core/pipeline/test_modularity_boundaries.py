#!/usr/bin/env python3
"""Negative controls for pipeline single-source-of-truth boundaries."""

from __future__ import annotations

import runpy
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


def test_missing_canonical_stage_does_not_run_legacy_root_copy(tmp_path: Path) -> None:
    """A stale root implementation cannot mask a missing canonical stage."""
    repo_root = tmp_path / "minimal-fork"
    project_dir = repo_root / "projects" / "p" / "output"
    project_dir.mkdir(parents=True)
    legacy = repo_root / "scripts" / "02_run_analysis.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("raise SystemExit(0)\n", encoding="utf-8")

    executor = PipelineExecutor(PipelineConfig(project_name="p", repo_root=repo_root))
    assert executor._run_script("scripts/pipeline/stage_02_analysis.py", "--project", "p") is False


def test_compatibility_entrypoints_reexport_canonical_implementations() -> None:
    """Compatibility files remain aliases, not independently drifting CLIs."""
    from scripts import execute_pipeline as compatibility_pipeline
    from scripts.pipeline.stage_06_llm_review import cli_main as canonical_llm_cli
    from scripts.pipeline.stage_07_executive_report import main as canonical_report_main
    from scripts.runner import execute_pipeline as canonical_pipeline

    assert compatibility_pipeline.execute_pipeline is canonical_pipeline.execute_pipeline
    assert compatibility_pipeline.execute_single_stage is canonical_pipeline.execute_single_stage
    assert compatibility_pipeline.handle_hitl_command is canonical_pipeline.handle_hitl_command
    assert compatibility_pipeline.main is canonical_pipeline.main

    repo_root = Path(__file__).parents[4]
    llm_wrapper = runpy.run_path(str(repo_root / "scripts/06_llm_review.py"), run_name="compatibility_test")
    report_wrapper = runpy.run_path(
        str(repo_root / "scripts/07_generate_executive_report.py"), run_name="compatibility_test"
    )
    assert llm_wrapper["cli_main"] is canonical_llm_cli
    assert report_wrapper["main"] is canonical_report_main


def test_compatibility_entrypoints_remain_directly_executable() -> None:
    """Consolidation must preserve the documented executable-script surface."""
    repo_root = Path(__file__).parents[4]
    for relative in (
        "scripts/execute_pipeline.py",
        "scripts/06_llm_review.py",
        "scripts/07_generate_executive_report.py",
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
