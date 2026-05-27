from pathlib import Path

from manuscript.sheaf import (
    SheafSection,
    build_coverage_matrix,
    list_registered_tracks,
    load_manifest,
    load_track_registry,
    track_order_for_section,
)


def test_registry_defines_track_order() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    assert registry.tracks["prose"].order < registry.tracks["ontology"].order
    assert registry.tracks["animation"].optional is True
    assert registry.tracks["layers"].optional is True
    assert registry.renderer_suffixes["ontology_yaml"] == (".yaml", ".yml")


def test_list_registered_tracks() -> None:
    root = Path(__file__).resolve().parents[1]
    specs = list_registered_tracks(root)
    assert {s.id for s in specs} >= {"prose", "lean", "ontology", "animation"}


def test_track_order_respects_section_include_exclude() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = next(s for s in manifest.sections if s.id == "methods_pymdp")
    ordered = track_order_for_section(section, registry)
    assert ordered.index("prose") < ordered.index("pymdp")
    assert "gnn" in ordered


def test_section_custom_track_order() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    section = SheafSection(
        id="demo",
        title="Demo",
        short="demo",
        order=1,
        tracks={"prose": "a", "formalism": "b", "lean": "c"},
        output_name="01_demo.md",
        track_order=("lean", "prose"),
    )
    assert track_order_for_section(section, registry) == ["lean", "prose"]


def test_full_section_binds_all_registry_tracks() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    full = next(s for s in manifest.sections if s.id == "appendix_full_sheaf")
    assert "layers" not in full.tracks
    assert set(full.tracks) == set(registry.tracks) - {"layers"}


def test_methods_sheaf_binds_layers_tracks() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    section = next(s for s in manifest.sections if s.id == "methods_sheaf")
    assert section.track_order == ("prose", "formalism", "visualization", "layers")
    assert "visualization" in section.tracks
    assert "layers" in section.tracks
    assert "formalism" in section.tracks
    registry = load_track_registry(root / manifest.registry_path)
    assert registry.tracks["visualization"].renderer == "section_figures"
    assert registry.tracks["layers"].renderer == "layers_report"


def test_discussion_outlook_binds_simulation_and_ontology() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = load_manifest(root / "manuscript" / "sheaf" / "manifest.yaml")
    section = next(s for s in manifest.sections if s.id == "discussion_outlook")
    assert "simulation" in section.tracks
    assert "ontology" in section.tracks
    matrix = build_coverage_matrix(
        load_track_registry(root / manifest.registry_path),
        manifest,
        root,
    )
    row = next(r for r in matrix.sections if r.section_id == "discussion_outlook")
    bound_tracks = {cell.track_id for cell in row.cells if cell.bound}
    assert {"prose", "simulation", "ontology"}.issubset(bound_tracks)
