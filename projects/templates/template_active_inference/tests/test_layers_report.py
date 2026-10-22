"""Tests for sheaf layers markdown tables."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from manuscript.sheaf.coverage import build_coverage_matrix
from manuscript.sheaf.layers_report import (
    render_binding_matrix_table,
    render_sheaf_layers_markdown,
    render_track_improvement_scope_table,
    render_track_lane_matrix_table,
    render_track_registry_table,
    render_track_status_table,
)
from manuscript.sheaf.manifest import load_manifest
from manuscript.sheaf.models import coverage_cell_symbol
from manuscript.sheaf.registry import load_track_registry
from manuscript.sheaf.status import build_sheaf_section_status_matrix


def _humanized(value: object) -> str:
    return " ".join(str(value).replace("_", " ").replace("-", " ").replace(".", " ").split())


def _basename(value: object) -> str:
    return " ".join(Path(str(value)).name.replace("_", " ").split())


def _table_rows(markdown: str) -> list[str]:
    lines = [line for line in markdown.splitlines() if line.startswith("|")]
    assert lines
    assert all(line.count("|") == 4 for line in lines)
    return lines[2:]


def _first_cells(lines: list[str]) -> list[str]:
    cells = [line.strip("|").split("|", maxsplit=1)[0].strip() for line in lines]
    return [cell.removeprefix("**").removesuffix("**") for cell in cells]


def test_coverage_cell_symbol_maps_colors() -> None:
    assert coverage_cell_symbol("black") == "P"
    assert coverage_cell_symbol("gray") == "M"
    assert coverage_cell_symbol("white") == "—"


def test_track_registry_table_row_count(project_root: Path) -> None:
    manifest = load_manifest(project_root / "manuscript" / "sheaf" / "manifest.yaml", project_root=project_root)
    registry = load_track_registry(project_root / manifest.registry_path)
    original_labels = {track_id: spec.label for track_id, spec in registry.tracks.items()}
    table = render_track_registry_table(registry)
    assert "<!-- sheaf-layers:registry -->" in table
    assert "## Sheaf fragment track registry" in table
    cells = [
        [cell.strip() for cell in line.strip("|").split("|")] for line in table.splitlines() if line.startswith("|")
    ]
    assert cells[0] == ["Order", "Track id", "Label", "Renderer", "Paper role", "Paper use", "Optional"]
    assert all(len(row) == len(cells[0]) for row in cells)
    ordered_tracks = sorted(registry.tracks.items(), key=lambda item: item[1].order)
    assert len(cells[2:]) == len(ordered_tracks)
    for row, (track_id, spec) in zip(cells[2:], ordered_tracks, strict=True):
        assert row[:2] == [str(spec.order), f"`{track_id}`"]
        assert row[2].replace(" / ", "/") == spec.label
        assert row[3:] == [
            f"`{spec.renderer}`",
            spec.paper_role,
            spec.paper_use,
            "Yes" if spec.optional else "No",
        ]
        # Ordinary Markdown spaces provide line-break opportunities in PDF and HTML.
        # Exact rendered geometry is checked by native publication QA separately.
        for index, character in enumerate(row[2]):
            if character == "/":
                assert row[2][index - 1 : index] == " "
                assert row[2][index + 1 : index + 2] == " "
    assert {track_id: spec.label for track_id, spec in registry.tracks.items()} == original_labels
    assert "**Track count:** {{sheaf_track_count}} registered fragment types." in table


def test_binding_matrix_totals_use_tokens(project_root: Path) -> None:
    manifest = load_manifest(project_root / "manuscript" / "sheaf" / "manifest.yaml", project_root=project_root)
    registry = load_track_registry(project_root / manifest.registry_path)
    matrix = build_coverage_matrix(registry, manifest, project_root)
    table = render_binding_matrix_table(matrix, manifest, project_root=project_root)
    assert "<!-- sheaf-layers:binding-matrix -->" in table
    assert "## IMRAD binding matrix" in table
    assert "{{coverage_present}} present" in table
    assert "{{coverage_bound}} bound" in table
    assert "{{coverage_missing}} missing" in table
    assert "| Section | Present tracks (P) | Missing tracks (M) |" in table
    assert "Every track not listed for a row is absent (not bound)." in table
    assert "`output/data/sheaf_coverage_matrix.json`" in table
    assert "[@fig:sheaf_coverage_heatmap]" in table


def test_binding_matrix_summary_is_complete_and_deterministic(project_root: Path) -> None:
    manifest = load_manifest(project_root / "manuscript" / "sheaf" / "manifest.yaml", project_root=project_root)
    registry = load_track_registry(project_root / manifest.registry_path)
    matrix = build_coverage_matrix(registry, manifest, project_root)

    first = render_binding_matrix_table(matrix, manifest, project_root=project_root)
    second = render_binding_matrix_table(matrix, manifest, project_root=project_root)
    assert first == second

    table_lines = [line for line in first.splitlines() if line.startswith("|")]
    assert table_lines
    assert all(line.count("|") == 4 for line in table_lines)

    data_lines = table_lines[2:]
    assert len(data_lines) == len(matrix.sections)
    for row, line in zip(matrix.sections, data_lines, strict=True):
        section_text, present_text, missing_text = [part.strip() for part in line.strip("|").split("|")]
        expected_section = f"{'↳ ' * row.depth}{row.title}"
        if row.kind == "group":
            expected_section = f"**{expected_section} (group)**"
        assert section_text == expected_section
        cells_by_track = {cell.track_id: cell for cell in row.cells}
        present = [track_id for track_id in matrix.track_ids if cells_by_track[track_id].status == "present"]
        missing = [track_id for track_id in matrix.track_ids if cells_by_track[track_id].status == "missing"]
        absent = [track_id for track_id in matrix.track_ids if cells_by_track[track_id].status == "absent"]
        bound = [track_id for track_id in matrix.track_ids if cells_by_track[track_id].bound]

        assert set(present).isdisjoint(missing)
        assert set(present) | set(missing) == set(bound)
        assert set(absent) == set(matrix.track_ids) - set(bound)
        assert present_text == (", ".join(f"`{track_id}`" for track_id in present) or "—")
        assert missing_text == (", ".join(f"`{track_id}`" for track_id in missing) or "—")


def test_track_lane_summary_preserves_every_canonical_row(project_root: Path) -> None:
    payload = json.loads((project_root / "output" / "data" / "track_lane_matrix.json").read_text(encoding="utf-8"))
    rows = payload["rows"]
    tracks_config = yaml.safe_load((project_root / "tracks.yaml").read_text(encoding="utf-8"))
    canonical_track_ids = [row["id"] for row in tracks_config["tracks"]]

    first = render_track_lane_matrix_table(project_root)
    assert render_track_lane_matrix_table(project_root) == first
    assert "output/data/track_lane_matrix.json" in first
    assert "remains the authority for exact source paths" in first

    table_rows = _table_rows(first)
    expected_track_ids = [row["track_id"] for row in rows]
    assert len(table_rows) == payload["row_count"] == len(rows)
    assert expected_track_ids == canonical_track_ids
    assert _first_cells(table_rows) == [_humanized(track_id) for track_id in expected_track_ids]
    assert set(payload["pipeline_track_ids"]) == set(expected_track_ids)
    assert all("`" not in line for line in table_rows)

    for row, line in zip(rows, table_rows, strict=True):
        assert _basename(row["producer"]) in line
        assert _basename(row["primary_artifact"]) in line
        assert all(_basename(source) in line for source in row["source_paths"])
        assert all(_humanized(gate) in line for gate in row["validation_gates"])
        assert _humanized(row["negative_control"]) in line


def test_track_improvement_summary_preserves_every_scope_row(project_root: Path) -> None:
    payload = json.loads(
        (project_root / "output" / "data" / "track_improvement_scope.json").read_text(encoding="utf-8")
    )
    rows = payload["improvement_roadmap"]
    registry = load_track_registry(project_root / "manuscript" / "sheaf" / "tracks.yaml")
    promotion_by_track = {row["track_id"]: row for row in payload["promotion_matrix"]}

    first = render_track_improvement_scope_table(project_root)
    assert render_track_improvement_scope_table(project_root) == first
    assert "output/data/track_improvement_scope.json" in first
    assert "remains the authority for exact priorities" in first

    table_rows = _table_rows(first)
    expected_track_ids = [row["track_id"] for row in rows]
    assert len(table_rows) == payload["improvement_row_count"] == len(rows)
    assert _first_cells(table_rows) == [_humanized(track_id) for track_id in expected_track_ids]
    assert set(registry.tracks).issubset(expected_track_ids)
    assert all("`" not in line for line in table_rows)

    for row, line in zip(rows, table_rows, strict=True):
        assert _basename(row["current_proof"]) in line
        assert _basename(row["next_proving_artifact"]) in line
        assert _humanized(row["status"]) in line
        assert _humanized(row["gate_or_predicate"]) in line
        assert _humanized(row["negative_control"]) in line
        promotion = promotion_by_track.get(row["track_id"])
        if promotion is None:
            assert "Producer: none while blocked." in line
        else:
            assert _basename(promotion["producer"]) in line


def test_track_status_table_preserves_rows_and_allocates_identifier_columns(project_root: Path) -> None:
    """Keep real status facts while giving their code identifiers enough table space."""
    payload = build_sheaf_section_status_matrix(project_root)
    markdown = render_track_status_table(project_root)
    table_lines = [line for line in markdown.splitlines() if line.startswith("|")]
    cells = [[cell.strip() for cell in line.strip("|").split("|")] for line in table_lines]
    assert cells[0] == ["Track", "Renderer", "Bound sections", "Present", "Missing", "Claims", "Status"]
    assert all(len(row) == len(cells[0]) for row in cells)
    assert [cell.endswith(":") for cell in cells[1]] == [False, False, True, True, True, True, False]
    expected_rows = [
        [
            f"`{row['track_id']}`",
            f"`{row['renderer']}`",
            str(row["bound_section_count"]),
            str(row["present_section_count"]),
            str(row["missing_section_count"]),
            str(row["claim_count"]),
            f"`{row['status']}`",
        ]
        for row in payload["tracks"]
    ]
    assert cells[2:] == expected_rows
    assert expected_rows
    assert f"**Status cells:** {payload['cell_count']} section-track cells." in markdown

    # Pandoc's default source-table width is 72 characters. Separator dash
    # weights express the relative space; this is a source-allocation control,
    # not a substitute for the real SDK PDF/HTML rendering and visual checks.
    def assert_code_columns_have_room(separator: str) -> None:
        fields = [cell.strip() for cell in separator.strip("|").split("|")]
        assert len(fields) == len(cells[0])
        assert all(set(cell) <= {"-", ":"} and cell.count("-") >= 3 for cell in fields)
        weights = [cell.count("-") for cell in fields]
        for column in (0, 1, 6):
            longest_identifier = max(len(row[column].strip("`")) for row in expected_rows)
            assert 72 * weights[column] >= longest_identifier * sum(weights), "code column is too narrow"

    assert max(map(len, table_lines)) > 72  # Ensure Pandoc uses the wrapped table route.
    assert_code_columns_have_room(table_lines[1])
    # Genuine prior layout: replay the separator that collided in the held PDF.
    with pytest.raises(AssertionError, match="code column is too narrow"):
        assert_code_columns_have_room("| --- | --- | ---: | ---: | ---: | ---: | --- |")


def test_render_sheaf_layers_markdown(project_root: Path) -> None:
    md = render_sheaf_layers_markdown(project_root)
    assert "Sheaf fragment track registry" in md
    assert "IMRAD binding matrix" in md
    assert "<!-- sheaf-layers:legend -->" in md
    assert "<!-- sheaf-layers:section-status -->" in md
    assert "<!-- sheaf-layers:track-status -->" in md
    assert "<!-- sheaf-layers:render-log -->" in md
    assert "| Symbol | Coverage color | Meaning |" in md
