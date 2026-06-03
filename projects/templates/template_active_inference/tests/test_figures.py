from pathlib import Path
import csv
import json
import re

import pytest
from PIL import Image

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from visualizations.figure_registry import figure_output_path, load_figure_registry, render_figure_markdown
from visualizations.figures import (
    FIGURE_GENERATORS,
    figure_ising_mi_curve,
    generate_all_figures,
    run_figure,
)
from visualizations.figures_sheaf import coverage_heatmap_payload, figure_sheaf_layers_overview


def _assert_png(path: Path, *, min_width: int = 400, min_height: int = 200) -> None:
    assert path.exists(), f"missing figure: {path}"
    assert path.stat().st_size > 5_000, f"figure too small: {path}"
    with Image.open(path) as img:
        width, height = img.size
        assert width >= min_width, f"{path.name} width {width} < {min_width}"
        assert height >= min_height, f"{path.name} height {height} < {min_height}"
        assert img.mode == "RGB", f"expected RGB after normalization, got {img.mode} for {path.name}"


def test_figure_generators_match_registry(project_root: Path) -> None:
    registry = load_figure_registry(project_root)
    assert set(FIGURE_GENERATORS) == set(registry)


def test_figure_registry_fail_closed_on_unknown_token(project_root: Path) -> None:
    with pytest.raises(ValueError, match="unresolved figure tokens"):
        render_figure_markdown(
            project_root,
            "sheaf_coverage_heatmap",
            variables={"sheaf_track_count": "30"},
        )


@pytest.mark.timeout(30)
def test_all_generators_write_png(project_root: Path) -> None:
    from analysis import run_analysis
    from manuscript.sheaf.coverage import emit_coverage_artifacts
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    emit_coverage_artifacts(project_root)

    for figure_id in FIGURE_GENERATORS:
        path = run_figure(figure_id, project_root)
        assert path == figure_output_path(project_root, figure_id)
        _assert_png(path)


def test_free_energy_grid_matches_ssot(project_root: Path) -> None:
    from analysis import run_analysis

    run_analysis(project_root)
    sweep_path = project_root / "output" / "data" / "parameter_sweep.csv"
    rows = list(csv.DictReader(sweep_path.open(newline="", encoding="utf-8")))
    grid = lambda_grid(load_hyperparameters())
    assert len(rows) == len(grid)


@pytest.mark.timeout(30)
def test_generate_all_figures_complete(project_root: Path) -> None:
    from analysis import run_analysis
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)

    paths = generate_all_figures(project_root)
    registry = load_figure_registry(project_root)
    expected_names = {spec.filename for spec in registry.values()}
    written_names = {path.name for path in paths if path.suffix == ".png"}
    assert expected_names.issubset(written_names)
    assert any(p.name == "sheaf_coverage_matrix.json" for p in paths)
    assert any(p.name == "figure_registry.json" for p in paths)


def test_figure_registry_json_matches_yaml(project_root: Path) -> None:
    from visualizations.figure_registry import build_figure_registry_payload, write_figure_registry_json

    registry = load_figure_registry(project_root)
    path = write_figure_registry_json(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {f"fig:{figure_id}" for figure_id in registry}
    for figure_id, spec in registry.items():
        record = payload[f"fig:{figure_id}"]
        assert record["filename"] == spec.filename
        assert record["generated_by"] == f"visualizations.figures::{figure_id}"


def test_figure_ising_mi_curve_dimensions(project_root: Path) -> None:
    from analysis import run_analysis

    run_analysis(project_root)
    path = figure_ising_mi_curve(project_root)
    _assert_png(path, min_width=600, min_height=250)


def test_figure_sheaf_layers_overview_dimensions(project_root: Path) -> None:
    from manuscript.sheaf.coverage import emit_coverage_artifacts

    emit_coverage_artifacts(project_root)
    payload = coverage_heatmap_payload(project_root)
    assert payload is not None
    path = figure_sheaf_layers_overview(project_root)
    assert path is not None
    _assert_png(path, min_width=900, min_height=500)


def test_appendix_formalism_uses_registry_tokens(project_root: Path) -> None:
    path = (
        project_root
        / "manuscript"
        / "sections"
        / "imrad"
        / "appendix_full_sheaf"
        / "formalism.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "{{appendix_sheaf_track_count}}" in text
    assert re.search(r"\|\s*\\mathcal\{T\}_\{.*full.*\}\s*\|\s*=\s*9", text) is None


def test_coverage_page_section_figures_registered(project_root: Path) -> None:
    from visualizations.figure_registry import load_section_figures

    refs = load_section_figures(project_root).get("coverage_page", ())
    assert refs and refs[0].figure_id == "sheaf_coverage_heatmap"
    assert refs[0].number is None
    # pandoc-crossref owns numbering: no hand-written caption prefix is emitted.
    assert refs[0].caption_prefix == ""


def test_figure_sheaf_coverage_heatmap_dimensions(project_root: Path) -> None:
    from manuscript.sheaf.coverage import emit_coverage_artifacts
    from visualizations.figures_sheaf import figure_sheaf_coverage_heatmap

    emit_coverage_artifacts(project_root)
    path = figure_sheaf_coverage_heatmap(project_root)
    assert path is not None
    _assert_png(path, min_width=700, min_height=400)


def test_coverage_heatmap_payload_none_without_sections(tmp_path: Path) -> None:
    assert coverage_heatmap_payload(tmp_path) is None
