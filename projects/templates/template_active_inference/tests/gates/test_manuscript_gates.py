"""Manuscript gate validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from gates.validation import validate_manuscript

from gate_support import ensure_gate_artifacts, refresh_generated_gate_artifacts

pytestmark = pytest.mark.timeout(300)


@pytest.mark.timeout(300)
def test_validate_manuscript_contract(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    ensure_gate_artifacts(project_root)
    write_resolved_manuscript(project_root, generate_variables(project_root, require_analysis_outputs=False))
    checks = validate_manuscript(project_root)
    assert checks["sheaf_manifest"]
    assert checks["sheaf_registry"]
    assert checks["sheaf_valid"]
    assert checks["coverage_matrix_valid"]
    assert checks["full_sheaf_appendix_tracks"]
    assert checks["imrad_groups_present"]
    assert checks["claim_ledger_valid"]
    assert checks["gnn_concordance"]
    assert checks["sheaf_coverage_page"]
    assert checks["sheaf_coverage_json"]
    assert checks["sheaf_coverage_heatmap"]
    assert checks["methods_sheaf_layers"]
    assert checks["manuscript_tokens_registered"]
    assert checks["resolved_manuscript_hydrated"]


def test_validate_manuscript_methods_sheaf_layers_negative(project_root: Path) -> None:
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "08_methods_sheaf.md"
    compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original.replace("<!-- sheaf-layers:registry -->", ""), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["methods_sheaf_layers"] is False
    finally:
        path.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        ("<!-- sheaf-layers:binding-matrix -->", ""),
        ("<!-- sheaf-layers:legend -->", ""),
        ("<!-- sheaf-layers:render-log -->", ""),
        ("sheaf_layers_overview.png", "broken_layers_overview.png"),
    ],
)
def test_validate_manuscript_methods_sheaf_layers_negative_markers(
    project_root: Path,
    needle: str,
    replacement: str,
) -> None:
    from manuscript.sheaf import compose_all_sections

    path = project_root / "manuscript" / "08_methods_sheaf.md"
    compose_all_sections(project_root)
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original.replace(needle, replacement), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["methods_sheaf_layers"] is False
    finally:
        path.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_full_sheaf_appendix_tracks_negative(project_root: Path) -> None:
    path = project_root / "manuscript" / "16_appendix_full_sheaf.md"
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original.replace("sheaf-track:prose", "sheaf-track:broken"), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["full_sheaf_appendix_tracks"] is False
    finally:
        path.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_resolved_hydrated_negative(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    resolved = project_root / "output" / "manuscript" / "00_abstract.md"
    if not resolved.is_file():
        write_resolved_manuscript(project_root, generate_variables(project_root, require_analysis_outputs=False))
    original = resolved.read_text(encoding="utf-8")
    try:
        resolved.write_text(original + "\n{{unresolved_test_token}}\n", encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["resolved_manuscript_hydrated"] is False
    finally:
        resolved.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_resolved_hydrated_allows_generated_latex_bookends(project_root: Path) -> None:
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables

    output_dir = write_resolved_manuscript(
        project_root,
        generate_variables(project_root, require_analysis_outputs=False),
    )
    begin = output_dir / "00_00_transmission_begin.md"
    original = begin.read_text(encoding="utf-8") if begin.is_file() else None
    try:
        begin.write_text("\\thispagestyle{empty}\n\\begin{samepage}\n", encoding="utf-8")

        checks = validate_manuscript(project_root)

        assert checks["resolved_manuscript_hydrated"] is True
    finally:
        if original is None:
            begin.unlink(missing_ok=True)
        else:
            begin.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_gnn_concordance_negative(project_root: Path) -> None:
    gnn = project_root / "gnn" / "bernoulli_toy.gnn.md"
    original = gnn.read_text(encoding="utf-8")
    try:
        gnn.write_text(original.replace("pi1=Stream1PolicyVector\n", ""), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["gnn_concordance"] is False
    finally:
        gnn.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_tokens_registered_negative(project_root: Path) -> None:
    path = project_root / "manuscript" / "00_abstract.md"
    original = path.read_text(encoding="utf-8")
    try:
        path.write_text(original + "\n{{not_a_registered_token}}\n", encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["manuscript_tokens_registered"] is False
    finally:
        path.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)


def test_validate_manuscript_duplicate_track_marker_negative(project_root: Path) -> None:
    """A composed section with a doubled sheaf-track marker must fail the gate."""
    from manuscript.sheaf import compose_all_sections

    compose_all_sections(project_root)
    path = project_root / "manuscript" / "07_methods_lean.md"
    original = path.read_text(encoding="utf-8")
    marker = "<!-- sheaf-track:lean -->"
    assert marker in original
    try:
        # Plant a second standalone copy of an already-present marker (the stutter bug).
        path.write_text(original.replace(marker, marker + "\n\n" + marker, 1), encoding="utf-8")
        checks = validate_manuscript(project_root)
        assert checks["no_duplicate_sheaf_track_markers"] is False
    finally:
        path.write_text(original, encoding="utf-8")
        refresh_generated_gate_artifacts(project_root)
