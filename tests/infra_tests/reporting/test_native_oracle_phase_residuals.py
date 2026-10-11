"""Real JSON residual ledgers; no native owner or predicate is mocked."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from infrastructure.reporting.native_oracle_phase_residuals import (
    PHASE_RESIDUAL_SCHEMA,
    NativeOracleResidualGraphs,
    reconcile_native_phase_residual_graphs,
)


def _row(reason: str) -> dict[str, str]:
    return {
        "id": "pdf-visual-source-parity",
        "artifact_id": "manuscript:pdf",
        "axis": "full-page-parity",
        "reason": reason,
    }


def _join(original: object, reader: object, status: object, code: object) -> NativeOracleResidualGraphs:
    return reconcile_native_phase_residual_graphs(
        original,
        reader,
        original_status=status,
        original_exit_code=code,
        scope="templates/template_code_project",
        source_binding=("a" * 40, "b" * 64),
        original_run_id="c" * 32,
        artifact_contract_digest="d" * 64,
    )


def test_real_json_original_zero_with_current_gap_remains_blocking(tmp_path: Path) -> None:
    current_gap = _row("actual fresh Current full-page reference is unavailable")
    path = tmp_path / "checked-phase-graphs.json"
    path.write_text(json.dumps({"original": [], "reader": [current_gap]}))
    actual = json.loads(path.read_text())
    graphs = _join(actual["original"], actual["reader"], "pass", 0)
    assert graphs.data() == {
        "schema_version": PHASE_RESIDUAL_SCHEMA,
        "scope": "templates/template_code_project",
        "source_binding": ["a" * 40, "b" * 64],
        "original_run_id": "c" * 32,
        "artifact_contract_digest": "d" * 64,
        "original": [],
        "reader": [current_gap],
    }
    assert graphs.combined() == [current_gap]
    assert actual["original"] == []


def test_added_current_rows_preserve_complete_original_order_and_duplicate_occurrences() -> None:
    first, second, current = (
        _row("actual Original glyph gap"),
        _row("actual Original library gap"),
        _row("actual Current ink gap"),
    )
    original, reader = [first, first, second], [current, first, first, current, second]
    graphs = _join(original, reader, "blocked", 75)
    assert graphs.data()["original"] == original
    assert graphs.data()["reader"] == reader
    assert graphs.combined() == reader
    original[0]["reason"] = "changed caller row"
    assert graphs.data()["original"][0]["reason"] == "actual Original glyph gap"


@pytest.mark.parametrize(
    "original,reader",
    [
        ([_row("first")], []),
        ([_row("first")], [_row("changed Original")]),
        ([_row("first"), _row("second")], [_row("second"), _row("first")]),
        ([_row("first"), _row("first")], [_row("first")]),
    ],
)
def test_missing_changed_reordered_or_deduplicated_original_refuses(original: object, reader: object) -> None:
    with pytest.raises(ValueError, match="omitted, changed or reordered"):
        _join(original, reader, "blocked", 75)


@pytest.mark.parametrize(
    "status,code", [("pass", 0), ("blocked", 0), ("pass", 75), ("blocked", True), ("blocked", 124)]
)
def test_original_status_or_signed_exit_cannot_be_relabelled(status: object, code: object) -> None:
    row = _row("actual Original residual")
    with pytest.raises(ValueError, match="status/observed exit"):
        _join([row], [row], status, code)


@pytest.mark.parametrize("bad", [None, {}, [{"status": "pass"}], [{**_row("gap"), "fulfilled": "true"}]])
def test_missing_or_status_shaped_graph_is_not_checked_residual_data(bad: object) -> None:
    with pytest.raises(ValueError, match="exact row fields"):
        _join([], bad, "pass", 0)


def test_only_both_completed_empty_graphs_produce_an_empty_acceptance_union() -> None:
    assert _join([], [], "pass", 0).combined() == []
    row = _row("actual unresolved Original role")
    assert _join([row], [row], "blocked", 75).combined() == [row]
