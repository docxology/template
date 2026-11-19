"""Tests for generated artifact schema manifest coverage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from template_autoresearch_project.loop.models import AutoResearchLoopResult


@pytest.mark.slow
def test_generated_json_artifacts_have_schema_or_documented_exemption(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    manifest = json.loads((project_root / "output" / "data" / "autoresearch_schema_manifest.json").read_text())

    assert manifest["schema"] == "template-autoresearch-schema-manifest-v1"
    assert manifest["missing_schema_artifacts"] == []
    schema_paths = {row["path"] for row in manifest["schema_artifacts"]}
    exempt_paths = {row["path"] for row in manifest["generic_table_exemptions"]}
    required_json = {
        rel_path for rel_path in autoresearch_loop_result.config.required_artifacts if rel_path.endswith(".json")
    }
    assert required_json <= (schema_paths | exempt_paths)
    assert "output/data/autoresearch_review_packet.json" in schema_paths
    assert "output/data/review_decisions.json" in schema_paths
    assert "output/data/research_object_manifest.json" in schema_paths
    assert "output/data/autoresearch_phase_ledger.json" in schema_paths
    assert "output/data/figure_quality_report.json" in schema_paths
    assert "output/data/ml_candidate_rank_stability.json" in schema_paths
    assert "output/data/ml_calibration_bin_intervals.json" in schema_paths
    assert "output/reports/evidence_registry.json" in schema_paths


@pytest.mark.slow
def test_research_object_manifest_records_local_boundaries(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    payload = json.loads((project_root / "output" / "data" / "research_object_manifest.json").read_text())

    assert payload["schema"] == "template-autoresearch-research-object-manifest-v2"
    assert payload["project_name"] == "template_autoresearch_project"
    assert payload["artifact_count"] > 0
    assert payload["approval_state"]["publication_approved"] is False
    assert payload["source_ledger"]["path"] == "manuscript/source_ledger.yaml"
    assert payload["schema_manifest"]["path"] == "output/data/autoresearch_schema_manifest.json"
    assert any(row["path"] == "output/data/autoresearch_phase_ledger.json" for row in payload["artifacts"])
    assert any(row["path"] == "output/data/figure_quality_report.json" for row in payload["artifacts"])
    assert "does not claim RO-Crate" in payload["claim_boundary"]
    assert payload["artifact_count"] == len(payload["artifacts"])
    assert payload["artifact_count"] == payload["checksum_artifact_count"] + payload["derivative_reference_count"]
    records = [
        *payload["artifacts"],
        *payload["manuscript_outputs"],
        payload["evidence_registry"],
        payload["source_ledger"],
        payload["schema_manifest"],
    ]
    for record in records:
        if record["record_kind"] == "derivative_reference":
            assert set(record) == {"path", "record_kind", "integrity_authority"}
            assert record["integrity_authority"] == "output/reports/artifact_manifest.json"
        else:
            actual = (project_root / record["path"]).read_bytes()
            assert record["sha256"] == hashlib.sha256(actual).hexdigest()
            assert record["size_bytes"] == len(actual)
            assert record["empty"] == (not actual)
    primary_reference = next(
        row for row in payload["artifacts"] if row["path"] == "output/reports/artifact_manifest.json"
    )
    assert primary_reference["record_kind"] == "derivative_reference"

    inventory = json.loads((project_root / "output/data/autoresearch_supply_chain_inventory.json").read_text())
    exported = json.loads((project_root / "output/data/autoresearch_inventory_export.json").read_text())
    for record in [*inventory["inputs"], *inventory["generated_artifacts"], *exported["components"]]:
        path = project_root / record["path"]
        if path.is_file():
            actual = path.read_bytes()
            assert record["sha256"] == hashlib.sha256(actual).hexdigest()
            if "size_bytes" in record:
                assert record["size_bytes"] == len(actual)
    attestation = json.loads((project_root / "output/data/autoresearch_integrity_attestation.json").read_text())
    assert attestation["status"] == "passed"
    for record in attestation["checks"]:
        actual = hashlib.sha256((project_root / record["path"]).read_bytes()).hexdigest()
        assert record["expected_sha256"] == record["actual_sha256"] == actual


def test_final_hydration_recomputes_identically(
    project_root: Path, autoresearch_loop_result: AutoResearchLoopResult
) -> None:
    from template_autoresearch_project.manuscript.manuscript_tokens_core import compute_variables_and_provenance
    from template_autoresearch_project.manuscript.manuscript_tokens_figures import FIGURE_BLOCK_KEYS

    assert autoresearch_loop_result.readiness_valid
    variables, provenance = compute_variables_and_provenance(project_root, require_valid=True)
    data = project_root / "output/data"
    assert json.loads((data / "manuscript_variables.json").read_text()) == variables
    assert json.loads((data / "manuscript_variable_provenance.json").read_text()) == provenance
    assert json.loads((data / "manuscript_figure_blocks.json").read_text()) == {
        key: variables[key] for key in sorted(FIGURE_BLOCK_KEYS) if key in variables
    }
