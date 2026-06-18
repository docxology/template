from pathlib import Path

import pytest

from manuscript.sheaf import (
    SheafSection,
    build_coverage_matrix,
    list_registered_tracks,
    load_manifest,
    load_track_registry,
    track_order_for_section,
)


pytestmark = [pytest.mark.long_running, pytest.mark.timeout(120)]

def test_registry_defines_track_order() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    assert registry.tracks["prose"].order < registry.tracks["ontology"].order
    assert registry.tracks["animation"].optional is True
    assert registry.tracks["layers"].optional is True
    assert registry.renderer_suffixes["ontology_yaml"] == (".yaml", ".yml")


def test_registry_declares_paper_roles() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    assert registry.tracks
    for track_id, spec in registry.tracks.items():
        assert spec.paper_role, f"{track_id} missing general paper role"
        assert spec.paper_use, f"{track_id} missing paper-specific use"
        assert len(spec.paper_role.split()) >= 3
        assert len(spec.paper_use.split()) >= 5


def test_layers_report_exposes_track_roles() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = load_track_registry(root / "manuscript" / "sheaf" / "tracks.yaml")
    from manuscript.sheaf.layers_report import render_track_registry_table

    table = render_track_registry_table(registry)
    assert "| Order | Track id | Label | Renderer | Paper role | Paper use | Optional |" in table
    assert "Supports the narrative spine" in table
    assert "Injects registry figures into section-specific evidence blocks" in table


def test_list_registered_tracks() -> None:
    root = Path(__file__).resolve().parents[1]
    specs = list_registered_tracks(root)
    assert {s.id for s in specs} >= {
        "prose",
        "lean",
        "ontology",
        "animation",
        "evidence_fields",
        "release_bundle",
        "theorem_traceability",
        "gate_ergonomics",
    }
    assert not any(s.id.endswith(("_v2", "_v3", "_v4", "_v5")) for s in specs)


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
    assert section.track_order == (
        "prose",
        "formalism",
        "visualization",
        "provenance",
        "counterexample",
        "adversarial_audit",
        "evidence_fields",
        "release_bundle",
        "gate_ergonomics",
        "artifact_diffoscope",
        "artifact_license",
        "scholarship",
        "security_posture",
        "manuscript_staleness",
        "layers",
    )
    assert "visualization" in section.tracks
    assert "provenance" in section.tracks
    assert "counterexample" in section.tracks
    assert "adversarial_audit" in section.tracks
    assert "evidence_fields" in section.tracks
    assert "release_bundle" in section.tracks
    assert "gate_ergonomics" in section.tracks
    assert "artifact_diffoscope" in section.tracks
    assert "artifact_license" in section.tracks
    assert "scholarship" in section.tracks
    assert "manuscript_staleness" in section.tracks
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
