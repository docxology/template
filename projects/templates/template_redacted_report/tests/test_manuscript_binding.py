"""Manuscript-to-canonical-audit binding tests (fail closed on schema or value drift)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from redacted_report import AUDIT_SCHEMA, LEDGER_SCHEMA, load_release_fixture, write_release_artifacts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript"
RESULTS_MD = MANUSCRIPT_DIR / "02_results.md"
METHODS_MD = MANUSCRIPT_DIR / "01_methods.md"
EXAMPLE_INPUT = PROJECT_ROOT / "data" / "example_segments.json"
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"


def _regenerated_audit(tmp_path: Path) -> dict[str, object]:
    fixture = load_release_fixture(EXAMPLE_INPUT)
    paths = write_release_artifacts(EXAMPLE_INPUT, tmp_path)
    audit = json.loads(paths.redaction_audit.read_text(encoding="utf-8"))
    assert audit["source_fixture_sha256"] == fixture.source_fixture_sha256
    return audit


def test_audit_schema_fails_closed_on_change(tmp_path: Path) -> None:
    audit = _regenerated_audit(tmp_path)

    assert audit["schema_version"] == AUDIT_SCHEMA
    assert _regenerated_audit(tmp_path)["schema_version"] == AUDIT_SCHEMA


def test_ledger_schema_fails_closed_on_change(tmp_path: Path) -> None:
    fixture = load_release_fixture(EXAMPLE_INPUT)
    paths = write_release_artifacts(EXAMPLE_INPUT, tmp_path)
    ledger = json.loads(paths.release_ledger.read_text(encoding="utf-8"))

    assert ledger["schema_version"] == LEDGER_SCHEMA
    assert fixture.policy.name == "intelligence_release_review"


def test_manuscript_measured_table_matches_regenerated_audit(tmp_path: Path) -> None:
    audit = _regenerated_audit(tmp_path)
    prose = RESULTS_MD.read_text(encoding="utf-8")

    expected_rows = {
        "Segment count": str(audit["segment_count"]),
        "Redaction decision count": str(audit["decision_count"]),
        "Reviewer record count": str(audit["review_count"]),
        "Release safety score": str(audit["release_safety_score"]),
        "Redaction coverage": str(audit["redaction_coverage"]),
        "Mosaic risk score": str(audit["mosaic_risk_score"]),
        "Findings": f"{len(audit['findings'])} warning-level",
        "Releasable": str(audit["releasable"]).lower(),
        "Final release recommended": str(audit["final_release_recommended"]).lower(),
        "Approvals": str(audit["review_gate"]["approval_count"]),
    }
    for label, value in expected_rows.items():
        assert f"| {label} | {value} |" in prose, f"missing measured row: {label} = {value}"


def test_manuscript_prose_counts_match_regenerated_audit(tmp_path: Path) -> None:
    audit = _regenerated_audit(tmp_path)
    prose = RESULTS_MD.read_text(encoding="utf-8")

    assert f"{audit['segment_count']} segments" in prose or "fourteen segments" in prose
    assert f"{audit['decision_count']} redaction decisions" in prose or "Twenty-two redaction decisions" in prose
    assert str(audit["redaction_coverage"]) in prose
    assert audit["review_gate"]["approval_count"] == 3


def test_manuscript_figure_references_resolve_to_registry_and_disk() -> None:
    registry = json.loads((FIGURES_DIR / "figure_registry.json").read_text(encoding="utf-8"))
    combined_prose = RESULTS_MD.read_text(encoding="utf-8") + METHODS_MD.read_text(encoding="utf-8")

    assert set(registry) == {"fig:redaction_flow", "fig:disclosure_control_matrix"}
    for label in registry:
        assert label in combined_prose, f"manuscript never references {label}"
        assert f"../output/figures/{registry[label]['filename']}" in combined_prose
        assert (FIGURES_DIR / registry[label]["filename"]).is_file()


def test_stage_two_allowlist_matches_on_disk_scripts() -> None:
    config = yaml.safe_load((MANUSCRIPT_DIR / "config.yaml").read_text(encoding="utf-8"))
    allowlisted = config["analysis"]["scripts"]

    assert allowlisted == ["01_generate_release_artifacts.py", "02_build_figures.py"]
    for script in allowlisted:
        assert (PROJECT_ROOT / "scripts" / script).is_file()
