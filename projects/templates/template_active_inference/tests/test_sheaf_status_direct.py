"""Direct leg-deterministic tests for ``manuscript.sheaf.status``.

``validate_sheaf_status_outputs`` re-derives every stored aggregate from the
saved rows (PR#23 hardening) so a row-only forgery fails closed. On the tracked
snapshot the status matrix and render log validate cleanly, so those failure
arms -- missing files, schema mismatch, forged ``all_bound_fragments_present``,
incomplete status rows, failed render events -- only ran when a gate rebuilt
state. These tests settle an isolated project-tree copy once (writer-then-
validate), then inject one defect at a time into the written artifacts and
assert the exact issue string, restoring each mutation byte-for-byte.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from manuscript.sheaf.status import (
    RENDER_LOG_SCHEMA,
    STATUS_MATRIX_SCHEMA,
    build_sheaf_render_log,
    build_sheaf_section_status_matrix,
    validate_sheaf_status_outputs,
    write_sheaf_status_outputs,
)

from direct_recompute_support import copy_project_tree


@pytest.fixture(scope="module")
def settled_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Copy the tree and settle the status outputs once against the copy."""
    root = copy_project_tree(tmp_path_factory.mktemp("sheaf_status_tree"))
    write_sheaf_status_outputs(root)
    return root


@pytest.mark.timeout(300)
def test_writer_then_validate_is_clean(settled_root: Path) -> None:
    """After the in-session writer settles the copy, validation reports no issues."""
    assert validate_sheaf_status_outputs(settled_root) == []


@pytest.mark.timeout(300)
def test_build_matrix_is_self_consistent(settled_root: Path) -> None:
    """The matrix aggregates agree with a fresh re-derivation from its own rows."""
    matrix = build_sheaf_section_status_matrix(settled_root)
    assert matrix["schema"] == STATUS_MATRIX_SCHEMA
    assert matrix["cell_count"] == len(matrix["cells"])
    missing_cells = sum(1 for row in matrix["cells"] if row["coverage_status"] == "missing")
    assert matrix["missing_cell_count"] == missing_cells
    # all_bound_fragments_present is the re-derivation, not a bare stored True
    assert matrix["all_bound_fragments_present"] == (matrix["missing_required_count"] == 0)


@pytest.mark.timeout(300)
def test_render_log_all_events_ok_with_forcing_false_control(settled_root: Path) -> None:
    """all_events_ok is True on the settled copy and flips False when an input vanishes."""
    log = build_sheaf_render_log(settled_root)
    assert log["schema"] == RENDER_LOG_SCHEMA
    assert log["all_events_ok"] is True

    methods_sheaf = settled_root / "manuscript" / "08_methods_sheaf.md"
    original = methods_sheaf.read_bytes()
    try:
        methods_sheaf.unlink()
        broken = build_sheaf_render_log(settled_root)
        assert broken["all_events_ok"] is False
        assert any(
            event["event_id"] == "layers_renderer_bound" and event["status"] == "failed" for event in broken["events"]
        )
    finally:
        methods_sheaf.write_bytes(original)


def test_missing_outputs_are_reported(tmp_path: Path) -> None:
    """An empty root yields the two missing-artifact strings."""
    issues = validate_sheaf_status_outputs(tmp_path)
    assert "missing output/data/sheaf_section_status_matrix.json" in issues
    assert "missing output/reports/sheaf_render_log.json" in issues


@pytest.mark.timeout(300)
def test_status_matrix_schema_mismatch_is_reported(settled_root: Path) -> None:
    status_path = settled_root / "output" / "data" / "sheaf_section_status_matrix.json"
    original = status_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["schema"] = "not-the-status-schema"
        status_path.write_text(json.dumps(payload), encoding="utf-8")
        assert "sheaf_section_status_matrix.json schema mismatch" in validate_sheaf_status_outputs(settled_root)
    finally:
        status_path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_forged_all_bound_present_fails_closed(settled_root: Path) -> None:
    """A stored missing_required_count that contradicts the flag is caught."""
    status_path = settled_root / "output" / "data" / "sheaf_section_status_matrix.json"
    original = status_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["missing_required_count"] = 7  # contradicts all_bound_fragments_present == True
        status_path.write_text(json.dumps(payload), encoding="utf-8")
        assert "sheaf_section_status_matrix.json has missing bound fragments" in validate_sheaf_status_outputs(
            settled_root
        )
    finally:
        status_path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_incomplete_status_rows_fail_closed(settled_root: Path) -> None:
    """A section row with a blank status contradicts all_sections_have_status=True."""
    status_path = settled_root / "output" / "data" / "sheaf_section_status_matrix.json"
    original = status_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["sections"][0]["status"] = ""  # blank one section status; keep the True flag
        status_path.write_text(json.dumps(payload), encoding="utf-8")
        assert "sheaf_section_status_matrix.json has incomplete status rows" in validate_sheaf_status_outputs(
            settled_root
        )
    finally:
        status_path.write_text(original, encoding="utf-8")


@pytest.mark.timeout(300)
def test_render_log_schema_and_failed_events_are_reported(settled_root: Path) -> None:
    render_path = settled_root / "output" / "reports" / "sheaf_render_log.json"
    original = render_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(original)
        payload["schema"] = "not-the-render-schema"
        render_path.write_text(json.dumps(payload), encoding="utf-8")
        assert "sheaf_render_log.json schema mismatch" in validate_sheaf_status_outputs(settled_root)

        payload = json.loads(original)
        payload["events"][0]["status"] = "failed"  # contradicts all_events_ok=True
        render_path.write_text(json.dumps(payload), encoding="utf-8")
        assert "sheaf_render_log.json has failed render events" in validate_sheaf_status_outputs(settled_root)
    finally:
        render_path.write_text(original, encoding="utf-8")
