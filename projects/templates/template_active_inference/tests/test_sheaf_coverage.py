from pathlib import Path

from manuscript.sheaf import (
    build_coverage_matrix,
    classify_cell,
    emit_coverage_artifacts,
    gray_cell_count_from_json,
    load_coverage_json,
    load_manifest,
    load_track_registry,
    validate_coverage_json_data,
    write_coverage_json,
)
from manuscript.hydrate import collect_malformed_token_names
from orchestration.coverage_pipeline import run_coverage_pipeline
from visualizations.figure_registry import load_figure_registry, load_section_figures
from visualizations.figures import figure_sheaf_coverage_heatmap


def test_coverage_matrix_colors() -> None:
    assert classify_cell(track_id="prose", bound=False, rel_path=None, file_exists=False) == (
        "absent",
        "white",
    )
    assert classify_cell(track_id="prose", bound=True, rel_path="a.md", file_exists=True) == (
        "present",
        "black",
    )
    assert classify_cell(track_id="prose", bound=True, rel_path="a.md", file_exists=False) == (
        "missing",
        "gray",
    )


def test_heatmap_writes_png(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    matrix = build_coverage_matrix(registry, manifest, root)
    json_out = tmp_path / "output" / "data" / "sheaf_coverage_matrix.json"
    write_coverage_json(matrix, json_out)
    out = figure_sheaf_coverage_heatmap(tmp_path)
    assert out is not None
    assert out.exists()
    assert out.stat().st_size > 0


def test_emit_coverage_artifacts_writes_json_only(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    json_path = tmp_path / "output" / "data" / "matrix.json"
    json_out = emit_coverage_artifacts(root, json_path=json_path)
    assert json_out == json_path.resolve()
    assert json_out.exists()
    data = load_coverage_json(json_out)
    assert data.get("tracks")
    assert data.get("sections")


def test_run_coverage_pipeline_writes_json_and_png() -> None:
    root = Path(__file__).resolve().parents[1]
    json_out, png_out, page_out = run_coverage_pipeline(root)
    assert json_out.exists()
    assert png_out is not None
    assert png_out.exists()
    assert page_out is not None


def test_coverage_json_has_zero_gray_on_clean_tree() -> None:
    root = Path(__file__).resolve().parents[1]
    json_path = emit_coverage_artifacts(root)
    data = load_coverage_json(json_path)
    assert gray_cell_count_from_json(data) == 0
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    issues = validate_coverage_json_data(data, manifest, registry)
    assert not any(i.level == "error" for i in issues)


def test_coverage_json_includes_imrad_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    json_path = emit_coverage_artifacts(root)
    data = load_coverage_json(json_path)
    first = (data.get("sections") or [])[0]
    assert first.get("kind") == "group"
    assert first.get("imrad") == "introduction"
    assert first.get("depth") == 0


def test_write_coverage_page() -> None:
    root = Path(__file__).resolve().parents[1]
    _json_path, _png_path, path = run_coverage_pipeline(root)
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "Sheaf Track Coverage" in text
    assert "Introduction" in text
    assert "sheaf_coverage_heatmap.png" in text
    # pandoc-crossref owns numbering: one {#fig:} label with the caption text, no hand label.
    assert "{#fig:sheaf_coverage_heatmap" in text
    assert "Sheaf track coverage matrix:" in text
    assert "Coverage overview." not in text
    assert "Figure 4." not in text
    assert "Heatmap matrix of IMRAD manuscript rows" in text
    assert "16_appendix_full_sheaf.md" in text
    assert "{{appendix_sheaf_track_count}}" in text
    assert collect_malformed_token_names(text) == []
    assert "{{coverage_present}}" in text


def test_figure_registry_includes_si_and_layers_figures() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_figure_registry(root)
    assert "si_belief_entropy_curve" in registry
    assert "si_obs_action_trace" in registry
    assert "sheaf_layers_overview" in registry
    section_refs = load_section_figures(root)["results_si_tmaze"]
    assert any(ref.figure_id == "si_belief_entropy_curve" for ref in section_refs)
    sheaf_refs = load_section_figures(root)["methods_sheaf"]
    assert any(ref.figure_id == "sheaf_layers_overview" for ref in sheaf_refs)
    appendix_refs = load_section_figures(root)["appendix_full_sheaf"]
    assert any(ref.figure_id == "theorem_traceability_graph" for ref in appendix_refs)
    assert any(ref.figure_id == "causal_ablation_heatmap" for ref in appendix_refs)
