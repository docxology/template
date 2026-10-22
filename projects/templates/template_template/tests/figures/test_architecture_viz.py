"""Tests for template.architecture_viz module."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from infrastructure.validation.content.figure_validator import validate_figure_registry

from helpers import PROJECT_DIR, REPO_ROOT

from template_template.figures.architecture_viz import (
    comparative_feature_matrix_data,
    generate_all_architecture_figures,
    generate_architecture_overview,
    generate_comparative_feature_matrix,
    generate_module_inventory,
    generate_pipeline_stages,
)
from template_template.core.introspection import (
    ModuleInfo,
    PipelineStage,
    ProjectAnalysis,
    discover_infrastructure_modules,
    discover_projects,
)
from template_template.figures.figure_architecture_overview import _architecture_figure
from template_template.figures.viz_palette import FONT_FLOOR


def _sample_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(
            name="core",
            path=REPO_ROOT / "infrastructure/core",
            python_file_count=10,
            has_init=True,
            has_agents_md=True,
            has_readme_md=True,
            public_symbols=[],
        ),
        ModuleInfo(
            name="validation",
            path=REPO_ROOT / "infrastructure/validation",
            python_file_count=7,
            has_init=True,
            has_agents_md=True,
            has_readme_md=True,
            public_symbols=[],
        ),
    ]


def _sample_projects() -> list[ProjectAnalysis]:
    return [
        ProjectAnalysis(
            name="template_code_project",
            path=REPO_ROOT / "projects/templates/template_code_project",
            has_manuscript=True,
            chapter_count=8,
            has_tests=True,
            test_file_count=5,
            has_scripts=True,
            script_count=2,
            config={},
        ),
        ProjectAnalysis(
            name="template",
            path=PROJECT_DIR,
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
        PipelineStage(
            number=0,
            name="Setup",
            script_name="stage_00_setup.py",
            script_path=REPO_ROOT / "scripts/pipeline/stage_00_setup.py",
        ),
        PipelineStage(
            number=1,
            name="Run Tests",
            script_name="stage_01_test.py",
            script_path=REPO_ROOT / "scripts/pipeline/stage_01_test.py",
        ),
        PipelineStage(
            number=2,
            name="Run Analysis",
            script_name="stage_02_analysis.py",
            script_path=REPO_ROOT / "scripts/pipeline/stage_02_analysis.py",
        ),
    ]


def test_comparative_feature_matrix_data_shape_and_values() -> None:
    data, tools, capabilities = comparative_feature_matrix_data()
    assert data.shape == (14, 10)
    assert len(tools) == 10
    assert len(capabilities) == 14
    assert set(np.unique(data)).issubset({0.0, 0.5, 1.0})


def test_generate_architecture_overview_writes_png(tmp_path: Path) -> None:
    modules = discover_infrastructure_modules(REPO_ROOT)
    projects = discover_projects(REPO_ROOT)
    fig, ax = _architecture_figure(modules, projects, "v1.0.0")
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        cards = [patch for patch in ax.patches if patch.get_gid() == "architecture-card"]
        labels = [text for text in ax.texts if text.get_gid() == "architecture-card-label"]
        details = [text for text in ax.texts if text.get_gid() == "architecture-card-detail"]
        assert len(cards) == len(labels) == len(details) == len(modules) + len(projects)
        expected_names = [module.name for module in modules] + [
            project.name.removeprefix("template_") for project in projects
        ]
        assert [" ".join(text.get_text().split()) for text in labels] == [
            name.replace("_", " ") for name in expected_names
        ]
        boxes = [card.get_window_extent(renderer) for card in cards]
        for index, (box, label, detail) in enumerate(zip(boxes, labels, details, strict=True)):
            assert label.get_fontsize() >= FONT_FLOOR
            for text in (label, detail):
                extent = text.get_window_extent(renderer)
                assert box.contains(extent.x0, extent.y0), (
                    index,
                    text.get_text(),
                    "bottom/left",
                )
                assert box.contains(extent.x1, extent.y1), (
                    index,
                    text.get_text(),
                    "top/right",
                )
            assert not label.get_window_extent(renderer).overlaps(detail.get_window_extent(renderer))
            assert all(not box.overlaps(other) for other in boxes[index + 1 :])
    finally:
        plt.close(fig)
    path = generate_architecture_overview(modules, projects, tmp_path, "v1.0.0")
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

    registry_path = output_project_dir / "output" / "figures" / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["schema_version"] == "template-template-figure-registry-v1"
    figures = registry["figures"]
    assert {figure["filename"] for figure in figures} == {path.name for path in paths}
    assert {figure["label"] for figure in figures} == {
        "fig:template-architecture",
        "fig:template-pipeline-flow",
        "fig:template-module-inventory",
        "fig:template-comparative-matrix",
    }
    manuscript_dir = PROJECT_DIR / "manuscript"
    assert validate_figure_registry(registry_path, manuscript_dir, require_accessibility=True) == (True, [])

    paths[0].unlink()
    valid, issues = validate_figure_registry(registry_path, manuscript_dir, require_accessibility=True)
    assert not valid
    assert any("Registered generated figure file is missing" in issue and paths[0].name in issue for issue in issues)
