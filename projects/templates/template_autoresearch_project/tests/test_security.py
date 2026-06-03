"""Tests for local deterministic AutoResearch security artifacts."""

from __future__ import annotations

import ast
import shutil
from pathlib import Path

from infrastructure.autoresearch import SecurityProfile

from src.config import AutoResearchLoopConfig
from src.models import AutoResearchLoopResult
from src.security import (
    SECURITY_ARTIFACTS,
    integrity_attestation_payload,
    render_security_review_markdown,
    security_profile_payload,
    local_inventory_export_payload,
    supply_chain_inventory_payload,
    threat_model_payload,
    write_security_artifacts,
)


def _security_config() -> AutoResearchLoopConfig:
    return AutoResearchLoopConfig(
        topic="Security demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("readiness",),
        required_artifacts=(),
        quality_checks=("security_profile",),
        security_profile=SecurityProfile(
            enabled=True,
            threat_model_frameworks=("STRIDE", "MITRE_ATT&CK_T1195"),
        ),
    )


def test_security_profile_and_threat_model_payloads_are_bounded() -> None:
    config = _security_config()

    profile = security_profile_payload(config, generated_at="2026-05-26T00:00:00+00:00")
    threat_model = threat_model_payload(config, generated_at="2026-05-26T00:00:00+00:00")

    assert profile["enabled"] is True
    assert profile["network_policy"] == "default_offline"
    assert profile["external_signing"] is False
    assert profile["not_external_signing"] is True
    assert profile["not_slsa_certification"] is True
    assert profile["not_runtime_monitoring"] is True
    assert profile["not_network_security_assessment"] is True
    assert "No formal SBOM standard is emitted; the inventory is SBOM-style local metadata." in profile["non_claims"]
    assert threat_model["frameworks"] == ["STRIDE", "MITRE_ATT&CK_T1195"]
    assert threat_model["summary"]["asset_count"] == 7
    assert threat_model["summary"]["threat_count"] == 7
    assert threat_model["summary"]["control_count"] == 7
    assert {row["id"] for row in threat_model["controls"]} >= {"ctrl-offline", "ctrl-review", "ctrl-hashes"}


def test_inventory_and_attestation_report_pass_missing_and_mismatch_cases(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
    tmp_path: Path,
) -> None:
    existing_outputs = [
        project_root / rel_path
        for rel_path in autoresearch_loop_result.output_paths
        if (project_root / rel_path).exists()
    ]
    inventory = supply_chain_inventory_payload(
        project_root,
        existing_outputs[:5],
        generated_at="2026-05-26T00:00:00+00:00",
    )
    assert inventory["formal_sbom"] is False
    assert inventory["external_signing"] is False
    assert inventory["not_slsa_certification"] is True
    assert inventory["not_network_security_assessment"] is True
    assert any(row["id"] == "mnist_fixture" and row["exists"] for row in inventory["inputs"])
    assert inventory["generated_artifacts"]
    export = local_inventory_export_payload(inventory, generated_at="2026-05-26T00:00:00+00:00")
    assert export["schema"] == "template-autoresearch-local-inventory-export-v1"
    assert export["formal_sbom"] is False
    assert export["cyclonedx_complete"] is False
    assert export["component_count"] == len(export["components"])

    attestation = integrity_attestation_payload(
        project_root,
        inventory,
        generated_at="2026-05-26T00:00:00+00:00",
    )
    assert attestation["status"] == "passed"
    assert attestation["checked_count"] > 0
    assert attestation["external_signature"] is False
    assert attestation["not_external_signing"] is True
    assert attestation["not_runtime_monitoring"] is True

    observed = tmp_path / "observed.txt"
    observed.write_text("changed", encoding="utf-8")
    failed = integrity_attestation_payload(
        project_root,
        {
            "inputs": [
                {"path": str(observed), "required": True, "sha256": "0" * 64},
                {"path": str(tmp_path / "missing.txt"), "required": True, "sha256": ""},
                {"path": str(tmp_path / "optional.txt"), "required": False, "sha256": ""},
            ],
            "generated_artifacts": [],
        },
        generated_at="2026-05-26T00:00:00+00:00",
    )
    assert failed["status"] == "failed"
    # observed.txt (mismatch) + the project's MNIST provenance cross-check (passes).
    assert failed["checked_count"] == 2
    assert any(
        check["path"] == "data/mnist_small.npz" and check["status"] == "passed" for check in failed["checks"]
    )
    assert failed["missing_count"] == 1
    assert failed["mismatch_count"] == 1
    # "passed" is the project's MNIST provenance cross-check, appended to every attestation.
    assert {row["status"] for row in failed["checks"]} == {"missing", "mismatch", "passed"}


def test_write_security_artifacts_generates_local_review_and_figures(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
    tmp_path: Path,
) -> None:
    sandbox_project = tmp_path / "template_autoresearch_project"
    shutil.copytree(
        project_root,
        sandbox_project,
        ignore=shutil.ignore_patterns("output", ".pytest_cache", "__pycache__"),
    )
    sample_output = sandbox_project / "output" / "data" / "sample.json"
    sample_output.parent.mkdir(parents=True)
    sample_output.write_text('{"sample": true}\n', encoding="utf-8")
    config = _security_config()
    assert autoresearch_loop_result.readiness_valid is True
    output_paths = [sample_output]

    from infrastructure.autoresearch import BudgetPolicy

    from src.ml.task import run_bounded_ml_task

    ml_result = run_bounded_ml_task(sandbox_project, BudgetPolicy(max_iterations=4))
    paths = write_security_artifacts(
        sandbox_project,
        config,
        output_paths,
        generated_at="2026-05-26T00:00:00+00:00",
        ml_result=ml_result,
    )

    relative_paths = {path.relative_to(sandbox_project).as_posix() for path in paths}
    assert set(SECURITY_ARTIFACTS) == relative_paths
    assert (sandbox_project / "output" / "data" / "autoresearch_inventory_export.json").exists()
    assert (sandbox_project / "output" / "figures" / "autoresearch_security_control_matrix.png").stat().st_size > 1000
    assert (sandbox_project / "output" / "figures" / "autoresearch_integrity_chain.png").stat().st_size > 1000

    profile = security_profile_payload(config, generated_at="2026-05-26T00:00:00+00:00")
    threat_model = threat_model_payload(config, generated_at="2026-05-26T00:00:00+00:00")
    inventory = supply_chain_inventory_payload(
        sandbox_project,
        output_paths,
        generated_at="2026-05-26T00:00:00+00:00",
    )
    attestation = integrity_attestation_payload(
        sandbox_project,
        inventory,
        generated_at="2026-05-26T00:00:00+00:00",
    )
    markdown = render_security_review_markdown(profile, threat_model, inventory, attestation)
    assert "External signature: `false`" in markdown
    assert "No live network, LLM, or generated-code execution is part of the default path." in markdown


def test_default_runtime_files_do_not_import_network_clients(project_root: Path) -> None:
    exempt = {
        project_root / "src" / "mnist_fixture.py",
        project_root / "scripts" / "regenerate_mnist_fixture.py",
    }
    disallowed_modules = {"httpx", "requests", "selenium", "playwright", "socket", "urllib.request"}
    for path in [*sorted((project_root / "src").glob("*.py")), *sorted((project_root / "scripts").glob("*.py"))]:
        if path in exempt:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name for alias in node.names}
                assert disallowed_modules.isdisjoint(imported), f"{path} imports network/client module {imported}"
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module not in disallowed_modules, f"{path} imports from {node.module}"
            if isinstance(node, ast.Attribute):
                assert node.attr != "urlopen", f"{path} calls urlopen outside fixture maintenance tooling"
