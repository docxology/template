"""Tests for registry-backed figures."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable
from pathlib import Path

from infrastructure.validation.content.figure_validator import validate_figure_registry
from src.figures import write_all_figures
from src.figures.figure_registry import FIGURE_SPECS
from src.figures.sia_generation_heatmap import write_sia_generation_heatmap
from src.figures.sia_improvement_delta import write_sia_improvement_delta
from src.figures.sia_metrics import _fmt, write_sia_metric_progression
from src.loop import run_sia_loop_project

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Markdown sections that reference each figure (single source of truth for captions).
_MANUSCRIPT_SECTIONS = (
    PROJECT_ROOT / "manuscript" / "02_methodology.md",
    PROJECT_ROOT / "manuscript" / "03_results.md",
)

Copy = Callable[[Path], Path]


def _make_minimal_project(
    tmp_path: Path,
    copy_project_sandbox: Copy,
    *,
    generations: list[dict],  # type: ignore[type-arg]
) -> Path:
    """Create a sandbox project with a hand-crafted run_summary.json."""
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    summary_dir = project / "output" / "runs" / "run_1"
    summary_dir.mkdir(parents=True)
    payload = {
        "run_id": 1,
        "live": False,
        "max_generations": len(generations),
        "task_dir": str(project / "tasks" / "mini_classify"),
        "generations": generations,
    }
    (summary_dir / "run_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return project


def test_figures_are_deterministic_pngs():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    first = write_all_figures(PROJECT_ROOT)
    first_pngs = [path for path in first if path.suffix == ".png"]
    hashes_first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in first_pngs]
    second = write_all_figures(PROJECT_ROOT)
    second_pngs = [path for path in second if path.suffix == ".png"]
    hashes_second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in second_pngs]
    assert hashes_first == hashes_second
    for path in first_pngs:
        assert path.is_file()
        assert path.stat().st_size > 0
        assert path.suffix == ".png"
    assert PROJECT_ROOT / "output" / "figures" / "figure_registry.json" in first


def test_figure_specs_match_manuscript():
    """Each registered caption and filename must appear in the manuscript markdown.

    The figure registry NOTE asks captions to mirror the canonical manuscript
    captions; this enforces that contract so the two cannot silently drift.
    Markdown inline-code backticks are stripped before comparison because the
    manuscript wraps symbol names (e.g. ``write_sia_loop_topology``) in code spans.
    """
    combined = "".join(path.read_text(encoding="utf-8") for path in _MANUSCRIPT_SECTIONS).replace("`", "")
    for spec in FIGURE_SPECS:
        assert spec.filename in combined, f"figure file {spec.filename} not referenced"
        assert spec.caption in combined, f"caption drift for {spec.figure_id}"


def test_figure_registry_validates_manuscript_references():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    paths = write_all_figures(PROJECT_ROOT)
    registry = PROJECT_ROOT / "output" / "figures" / "figure_registry.json"

    ok, issues = validate_figure_registry(registry, PROJECT_ROOT / "manuscript")

    assert registry in paths
    assert ok, issues


# ── edge-case figure paths ───────────────────────────────────────────────────


def test_fmt_above_one():
    """_fmt must return a two-decimal float for values > 1.0 (non-percentage range)."""
    assert _fmt(1.5) == "1.50"
    assert _fmt(2.0) == "2.00"


def test_write_sia_generation_heatmap_empty_metrics(tmp_path: Path, copy_project_sandbox: Copy):
    """Empty run_summary (no generations) must produce a placeholder PNG without error."""
    project = _make_minimal_project(tmp_path, copy_project_sandbox, generations=[])
    out = write_sia_generation_heatmap(project)
    assert out.is_file()
    assert out.stat().st_size > 0
    assert out.suffix == ".png"


def test_write_sia_improvement_delta_single_generation(tmp_path: Path, copy_project_sandbox: Copy):
    """A single-generation run has no delta pairs — must produce a placeholder PNG."""
    project = _make_minimal_project(
        tmp_path,
        copy_project_sandbox,
        generations=[
            {
                "generation": 1,
                "evaluation": {"metric_name": "accuracy", "metric_value": 0.5, "n_samples": 6},
            }
        ],
    )
    out = write_sia_improvement_delta(project)
    assert out.is_file()
    assert out.stat().st_size > 0
    assert out.suffix == ".png"


def test_write_sia_metric_progression_single_generation(tmp_path: Path, copy_project_sandbox: Copy):
    """Single-generation run must produce a valid PNG (no shading band, no legend)."""
    project = _make_minimal_project(
        tmp_path,
        copy_project_sandbox,
        generations=[
            {
                "generation": 1,
                "evaluation": {"metric_name": "accuracy", "metric_value": 0.75, "n_samples": 6},
            }
        ],
    )
    out = write_sia_metric_progression(project)
    assert out.is_file()
    assert out.stat().st_size > 0


def test_write_sia_metric_progression_above_one_values(tmp_path: Path, copy_project_sandbox: Copy):
    """Metrics > 1.0 (e.g. F1 macro or raw counts) must use raw float formatting."""
    project = _make_minimal_project(
        tmp_path,
        copy_project_sandbox,
        generations=[
            {
                "generation": 1,
                "evaluation": {"metric_name": "score", "metric_value": 1.5, "n_samples": 6},
            },
            {
                "generation": 2,
                "evaluation": {"metric_name": "score", "metric_value": 1.8, "n_samples": 6},
            },
        ],
    )
    out = write_sia_metric_progression(project)
    assert out.is_file()
    assert out.stat().st_size > 0


def test_write_sia_metric_progression_empty_metrics(tmp_path: Path, copy_project_sandbox: Copy):
    """Zero-generation run must produce a valid PNG (empty values, no lines drawn)."""
    project = _make_minimal_project(tmp_path, copy_project_sandbox, generations=[])
    out = write_sia_metric_progression(project)
    assert out.is_file()
    assert out.stat().st_size > 0
