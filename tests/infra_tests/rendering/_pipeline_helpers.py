"""Shared helpers for the split pipeline test modules (formerly test_pipeline.py)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from infrastructure.rendering.pipeline import RenderPipelineDependencies


def _write_minimal_project_tree(project_root: Path) -> None:
    for sub in ("src", "tests", "scripts", "manuscript"):
        (project_root / sub).mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "manuscript" / "01_intro.md").write_text("# Intro", encoding="utf-8")


def _dependencies_for(project_root: Path, **overrides: object) -> RenderPipelineDependencies:
    """Return deterministic collaborators for focused orchestration tests."""
    dependencies = RenderPipelineDependencies(
        resolve_project=lambda _repo_root, _name: project_root,
        hydrate_manuscript=lambda _project_root, template_repo_root=None: 0,
        write_bookends=lambda _project_root, _project_name, repo_root: None,
        validate_latex=lambda report=None: 0,
        render_individual=lambda _manager, _source_files, _reporter: (0, []),
        render_combined=lambda *_args, **_kwargs: None,
        generate_summary=lambda project_name, repo_root=None: {
            "project": project_name,
            "combined_pdf": None,
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 0,
        },
        log_summary=lambda _summary: None,
        verify_outputs=lambda _project_name, repo_root=None: True,
    )
    return replace(dependencies, **overrides)


def _make_project_with_manuscript(project_root: Path, *, n_md: int = 1, n_figures: int = 0) -> None:
    """Populate a minimal project tree with real manuscript files."""
    for sub in ("src", "tests", "scripts", "manuscript", "output/figures"):
        (project_root / sub).mkdir(parents=True, exist_ok=True)
    (project_root / "src" / "__init__.py").write_text("", encoding="utf-8")
    (project_root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    for i in range(1, n_md + 1):
        (project_root / "manuscript" / f"0{i}_section.md").write_text(f"# Section {i}\n\nContent.\n", encoding="utf-8")
    for j in range(n_figures):
        fig = project_root / "output" / "figures" / f"fig_{j:02d}.png"
        fig.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
