from pathlib import Path
import csv
import json
import re

import pytest
from PIL import Image

from analytical.hyperparameters import lambda_grid, load_hyperparameters
from gate_support import temporary_json_mutation
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
        extrema = img.convert("RGB").getextrema()
        assert any(low != high for low, high in extrema), f"blank figure: {path.name}"
        aspect_ratio = width / height
        assert 0.45 <= aspect_ratio <= 4.2, f"{path.name} aspect ratio {aspect_ratio:.2f} outside bounds"


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
    from visualizations.figure_registry import write_figure_registry_json

    registry = load_figure_registry(project_root)
    path = write_figure_registry_json(project_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {f"fig:{figure_id}" for figure_id in registry}
    for figure_id, spec in registry.items():
        record = payload[f"fig:{figure_id}"]
        assert record["filename"] == spec.filename
        assert record["generated_by"] == f"visualizations.figures::{figure_id}"
        assert record["visual_role"] == spec.visual_role
        assert record["evidence_role"] == spec.evidence_role
        assert record["paper_claim"] == spec.paper_claim


def test_layout_sensitive_figures_have_publication_dimensions(project_root: Path) -> None:
    expected_minima = {
        "artifact_contract_map": (1800, 1400),
        "causal_ablation_heatmap": (1200, 700),
        "gnn_ontology_concordance": (1400, 650),
        "invariant_dashboard": (1300, 800),
        "multi_track_architecture": (1500, 1050),
        "scholarship_source_map": (1700, 950),
        "semantic_gluing_graph": (1450, 850),
        "security_posture_map": (1600, 850),
        "sheaf_coverage_heatmap": (2400, 900),
        "sheaf_layers_overview": (1800, 1400),
        "theorem_traceability_graph": (1450, 760),
        "track_lane_promotion_map": (1800, 1100),
        "lean_boundary_status": (1300, 900),
    }
    for figure_id, (min_width, min_height) in expected_minima.items():
        path = figure_output_path(project_root, figure_id)
        if not path.is_file():
            path = run_figure(figure_id, project_root)
        _assert_png(path, min_width=min_width, min_height=min_height)


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


def test_visualization_quality_audit_rejects_live_blank_render(project_root: Path) -> None:
    from roadmap_tracks.visualization_audit import (
        validate_visualization_quality_audit,
        write_visualization_quality_audit,
    )

    from analysis import run_analysis
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    run_figure("si_tmaze_actions", project_root)
    write_visualization_quality_audit(project_root)

    figure_path = project_root / "output" / "figures" / "si_tmaze_actions.png"
    original = figure_path.read_bytes()
    try:
        with Image.open(figure_path) as img:
            Image.new("RGB", img.size, "white").save(figure_path)
        issues = validate_visualization_quality_audit(project_root)
        assert any("blank" in issue or "live render" in issue for issue in issues)
    finally:
        figure_path.write_bytes(original)


def test_visualization_quality_audit_rejects_stale_section_and_source_rows(project_root: Path) -> None:
    from roadmap_tracks.visualization_audit import (
        validate_visualization_quality_audit,
        write_visualization_quality_audit,
    )

    write_visualization_quality_audit(project_root)
    audit_path = project_root / "output" / "reports" / "visualization_quality_audit.json"

    def break_source_and_section(payload: dict) -> None:
        payload["rows"][0]["section_bindings"] = []
        payload["rows"][0]["section_bound"] = True
        payload["rows"][0]["sources"] = []
        payload["rows"][0]["source_mapped"] = True
        payload["rows"][0]["source_backed"] = True

    with temporary_json_mutation(audit_path, break_source_and_section):
        issues = validate_visualization_quality_audit(project_root)

    assert any("section binding" in issue for issue in issues)
    assert any("source metadata" in issue for issue in issues)


def test_visualization_quality_audit_row_surface_and_hash_negative_control(project_root: Path) -> None:
    from roadmap_tracks.visualization_audit import (
        validate_visualization_quality_audit,
        write_visualization_quality_audit,
    )

    write_visualization_quality_audit(project_root)
    audit_path = project_root / "output" / "reports" / "visualization_quality_audit.json"
    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    registry = load_figure_registry(project_root)

    assert payload["figure_count"] == len(registry) == 23
    assert set(payload["rows"][0]) >= {
        "figure_id",
        "path",
        "sources",
        "source_mapped",
        "source_backed",
        "statistical_sources",
        "section_bindings",
        "section_bound",
        "visual_role",
        "visual_role_ok",
        "evidence_role",
        "evidence_role_ok",
        "paper_claim",
        "paper_claim_ok",
        "hash_present",
        "rendered",
        "width_px",
        "height_px",
        "mode",
        "nonblank",
        "complete",
        "quality_ok",
        "style_contract_ok",
    }
    assert payload["all_style_tokens_ok"] is True
    assert payload["all_figures_complete"] is True
    assert payload["style_contract"]["ok"] is True
    assert payload["style_contract"]["literal_issue_count"] == 0
    assert payload["all_auxiliary_outputs_classified"] is True
    assert payload["all_auxiliary_outputs_rendered"] is True

    def break_hash(payload: dict) -> None:
        payload["rows"][0]["hash_present"] = False
        payload["rows"][0]["complete"] = True
        payload["all_hashes_present"] = True
        payload["all_figures_complete"] = True

    with temporary_json_mutation(audit_path, break_hash):
        issues = validate_visualization_quality_audit(project_root)

    assert any("hash" in issue for issue in issues)

    def break_complete(payload: dict) -> None:
        payload["rows"][0]["complete"] = False
        payload["all_figures_complete"] = True

    with temporary_json_mutation(audit_path, break_complete):
        issues = validate_visualization_quality_audit(project_root)

    assert any("incomplete figure rows" in issue for issue in issues)


def test_visualization_quality_audit_rejects_style_and_auxiliary_forgery(project_root: Path) -> None:
    from roadmap_tracks.visualization_audit import (
        validate_visualization_quality_audit,
        write_visualization_quality_audit,
    )

    write_visualization_quality_audit(project_root)
    audit_path = project_root / "output" / "reports" / "visualization_quality_audit.json"

    def break_style_contract(payload: dict) -> None:
        payload["style_contract"]["rows"][0]["points"] = 1.0
        payload["style_contract"]["ok"] = True
        payload["all_style_tokens_ok"] = True
        payload["rows"][0]["style_contract_ok"] = True

    with temporary_json_mutation(audit_path, break_style_contract):
        issues = validate_visualization_quality_audit(project_root)

    assert any("style-token" in issue for issue in issues)

    def break_auxiliary_inventory(payload: dict) -> None:
        payload["auxiliary_visualizations"].append(
            {
                "path": "output/figures/untracked_visual.png",
                "filename": "untracked_visual.png",
                "classified": True,
                "classification": "forged",
                "producer": "none",
                "reason": "forged aggregate row",
                "rendered": True,
            }
        )
        payload["all_auxiliary_outputs_classified"] = True
        payload["all_auxiliary_outputs_rendered"] = True

    with temporary_json_mutation(audit_path, break_auxiliary_inventory):
        issues = validate_visualization_quality_audit(project_root)

    assert any("auxiliary visualizations" in issue for issue in issues)
