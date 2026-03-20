"""Tests for template.architecture_viz module."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from template.architecture_viz import (
    comparative_feature_matrix_data,
    generate_all_architecture_figures,
    generate_architecture_overview,
    generate_comparative_feature_matrix,
    generate_module_inventory,
    generate_pipeline_stages,
)
from template.introspection import ModuleInfo, PipelineStage, ProjectInfo

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT_DIR = Path(__file__).resolve().parents[1]


def _sample_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(
            name="core",
            path=Path("/tmp/core"),
            python_file_count=10,
            has_init=True,
            has_agents_md=True,
            has_readme_md=True,
            public_symbols=[],
        ),
        ModuleInfo(
            name="validation",
            path=Path("/tmp/validation"),
            python_file_count=7,
            has_init=True,
            has_agents_md=True,
            has_readme_md=True,
            public_symbols=[],
        ),
    ]


def _sample_projects() -> list[ProjectInfo]:
    return [
        ProjectInfo(
            name="code_project",
            path=Path("/tmp/code_project"),
            has_manuscript=True,
            chapter_count=8,
            has_tests=True,
            test_file_count=5,
            has_scripts=True,
            script_count=2,
            config={},
        ),
        ProjectInfo(
            name="template",
            path=Path("/tmp/template"),
            has_manuscript=True,
            chapter_count=8,
            has_tests=True,
            test_file_count=3,
            has_scripts=True,
            script_count=2,
            config={},
        ),
    ]


def _sample_stages() -> list[PipelineStage]:
    return [
        PipelineStage(number=0, name="Setup", script_name="00_setup_environment.py", script_path=Path("/tmp/00_setup_environment.py")),
        PipelineStage(number=1, name="Run Tests", script_name="01_run_tests.py", script_path=Path("/tmp/01_run_tests.py")),
        PipelineStage(number=2, name="Run Analysis", script_name="02_run_analysis.py", script_path=Path("/tmp/02_run_analysis.py")),
    ]


def test_comparative_feature_matrix_data_shape_and_values() -> None:
    data, tools, capabilities = comparative_feature_matrix_data()
    assert data.shape == (14, 10)
    assert len(tools) == 10
    assert len(capabilities) == 14
    assert set(np.unique(data)).issubset({0.0, 0.5, 1.0})


def test_generate_architecture_overview_writes_png(tmp_path: Path) -> None:
    path = generate_architecture_overview(_sample_modules(), _sample_projects(), tmp_path, "v1.0.0")
    assert path.exists()
    assert path.stat().st_size > 1000


def test_generate_pipeline_stages_writes_png(tmp_path: Path) -> None:
    path = generate_pipeline_stages(_sample_stages(), tmp_path)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_generate_module_inventory_writes_png(tmp_path: Path) -> None:
    path = generate_module_inventory(_sample_modules(), tmp_path)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_generate_comparative_feature_matrix_writes_png(tmp_path: Path) -> None:
    path = generate_comparative_feature_matrix(tmp_path)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_generate_all_architecture_figures_returns_four_paths(tmp_path: Path) -> None:
    output_project_dir = tmp_path / "project"
    output_project_dir.mkdir()
    paths = generate_all_architecture_figures(REPO_ROOT, output_project_dir)
    assert len(paths) == 4
    for path in paths:
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 1000
