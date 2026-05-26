"""Tests for generated artifact schema manifest coverage."""

from __future__ import annotations

import json
from pathlib import Path

from src.models import AutoResearchLoopResult


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


def test_research_object_manifest_records_local_boundaries(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    payload = json.loads((project_root / "output" / "data" / "research_object_manifest.json").read_text())

    assert payload["schema"] == "template-autoresearch-research-object-manifest-v1"
    assert payload["project_name"] == "template_autoresearch_project"
    assert payload["artifact_count"] > 0
    assert payload["approval_state"]["publication_approved"] is False
    assert payload["source_ledger"]["path"] == "manuscript/source_ledger.yaml"
    assert payload["schema_manifest"]["path"] == "output/data/autoresearch_schema_manifest.json"
    assert "does not claim RO-Crate" in payload["claim_boundary"]
