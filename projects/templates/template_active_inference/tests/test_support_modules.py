"""RunLogger and small support-module tests."""

from __future__ import annotations

import shutil
from pathlib import Path

from ontology.bindings import load_section_ontology, validate_gnn_ontology
from simulation.logging_utils import RunLogger


def test_run_logger_emit_and_records(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "runs.jsonl")
    log.fresh()
    log.emit({"event": "test", "value": 1})
    records = log.records()
    assert len(records) == 1
    assert records[0]["event"] == "test"


def test_run_logger_emit_recreates_missing_parent_after_fresh(tmp_path: Path) -> None:
    log = RunLogger(tmp_path / "logs" / "runs.jsonl")
    log.fresh()
    shutil.rmtree(log.path.parent)

    log.emit({"event": "test", "value": 2})

    assert log.records()[0]["value"] == 2


def test_sheaf_package_exports_public_symbols() -> None:
    from manuscript.sheaf import (
        GENERATED_RENDERERS,
        ImradBlock,
        SectionKind,
        coverage_cell_symbol,
        resolve_track_body,
    )

    assert coverage_cell_symbol("black") == "P"
    assert "section_figures" in GENERATED_RENDERERS
    assert resolve_track_body.__name__ == "resolve_track_body"
    assert ImradBlock is not None
    assert SectionKind is not None


def test_ontology_helpers() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "manuscript" / "sections" / "imrad" / "intro_contributions" / "ontology.yaml"
    terms = load_section_ontology(path)
    assert "location" in terms
    discussion = root / "manuscript" / "sections" / "imrad" / "discussion_outlook" / "ontology.yaml"
    discussion_terms = load_section_ontology(discussion)
    assert discussion_terms["pedagogical_scope"] == "Pedagogical scope"
    gnn = root / "gnn" / "bernoulli_toy.gnn.md"
    assert not validate_gnn_ontology(gnn)
