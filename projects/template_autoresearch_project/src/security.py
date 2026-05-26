"""Local deterministic security artifacts for the AutoResearch exemplar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.artifacts import compute_sha256

from .config import AutoResearchLoopConfig
from .figures import write_security_control_matrix_figure, write_security_integrity_chain_figure

SECURITY_ARTIFACTS = (
    "output/data/autoresearch_security_profile.json",
    "output/data/autoresearch_threat_model.json",
    "output/data/autoresearch_supply_chain_inventory.json",
    "output/data/autoresearch_integrity_attestation.json",
    "output/reports/autoresearch_security_review.md",
    "output/figures/autoresearch_security_control_matrix.png",
    "output/figures/autoresearch_integrity_chain.png",
)


def write_security_artifacts(
    project_root: Path,
    config: AutoResearchLoopConfig,
    output_paths: list[Path],
    *,
    generated_at: str,
) -> list[Path]:
    """Write local security profile, threat model, inventory, attestation, report, and figures."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    profile = security_profile_payload(config, generated_at=generated_at)
    threat_model = threat_model_payload(config, generated_at=generated_at)
    inventory = supply_chain_inventory_payload(project_root, output_paths, generated_at=generated_at)
    attestation = integrity_attestation_payload(project_root, inventory, generated_at=generated_at)
    review_markdown = render_security_review_markdown(profile, threat_model, inventory, attestation)

    paths = [
        _write_json(data_dir / "autoresearch_security_profile.json", profile),
        _write_json(data_dir / "autoresearch_threat_model.json", threat_model),
        _write_json(data_dir / "autoresearch_supply_chain_inventory.json", inventory),
        _write_json(data_dir / "autoresearch_integrity_attestation.json", attestation),
        _write_text(reports_dir / "autoresearch_security_review.md", review_markdown),
        write_security_control_matrix_figure(figures_dir, threat_model),
        write_security_integrity_chain_figure(figures_dir, attestation),
    ]
    return paths


def security_profile_payload(config: AutoResearchLoopConfig, *, generated_at: str) -> dict[str, object]:
    """Return the configured local security posture."""
    profile = config.security_profile
    frameworks = tuple(profile.threat_model_frameworks or ("STRIDE", "MITRE_ATT&CK_T1195"))
    return {
        "schema": "template-autoresearch-security-profile-v1",
        "generated_at": generated_at,
        "enabled": profile.enabled,
        "mode": profile.mode,
        "threat_model_frameworks": list(frameworks),
        "integrity_algorithm": profile.integrity_algorithm,
        "network_policy": profile.network_policy,
        "external_signing": profile.external_signing,
        "claim_scope": "Local research-artifact integrity evidence for this deterministic public exemplar",
        "non_claims": [
            "No external signing or Sigstore verification is performed by the default run.",
            "No formal SBOM standard is emitted; the inventory is SBOM-style local metadata.",
            "No production-grade SLSA compliance, SOC monitoring, or deployment hardening is claimed.",
            "No live network, LLM, or generated-code execution is part of the default path.",
        ],
        "reference_frameworks": [
            {
                "id": "NIST_SP_800_207",
                "scope": "Zero-trust design analogy for explicit verification boundaries.",
            },
            {
                "id": "NIST_SP_800_218_SSDF",
                "scope": "Secure development practice analogy for controlled inputs and review surfaces.",
            },
            {
                "id": "SLSA_SPEC",
                "scope": "Supply-chain provenance analogy; local checksums do not equal signed provenance.",
            },
            {
                "id": "MITRE_ATTACK_T1195",
                "scope": "Supply-chain compromise technique used to scope local artifact tamper risks.",
            },
        ],
    }


def threat_model_payload(config: AutoResearchLoopConfig, *, generated_at: str) -> dict[str, object]:
    """Return a small STRIDE and ATT&CK-scoped threat model for local artifacts."""
    frameworks = list(config.security_profile.threat_model_frameworks or ("STRIDE", "MITRE_ATT&CK_T1195"))
    assets = [
        _asset("asset-dataset", "Local MNIST fixture", "data/mnist_small.npz", "input data"),
        _asset("asset-task-config", "MNIST task configuration", "mnist_task.yaml", "experiment config"),
        _asset("asset-source", "Project source code", "src/", "implementation"),
        _asset("asset-generated", "Generated output artifacts", "output/", "result evidence"),
        _asset("asset-hydration", "Manuscript hydration", "output/data/manuscript_variables.json", "publication"),
        _asset("asset-review", "Review gates and packets", "output/data/review_decisions.json", "governance"),
        _asset("asset-ci", "CI and local build assumptions", "pipeline.yaml", "build context"),
    ]
    threats = [
        _threat(
            "threat-dataset-tamper",
            "asset-dataset",
            "Tampering",
            "T1195",
            "A local fixture could be replaced or edited before analysis.",
            ("sha256 fixture provenance", "artifact inventory", "default offline policy"),
            "Residual risk remains if a reviewer ignores checksum drift.",
        ),
        _threat(
            "threat-config-drift",
            "asset-task-config",
            "Tampering",
            "T1195.001",
            "Task settings could silently change candidate scope, budgets, or diagnostic policy.",
            ("git-reviewed config", "required artifact manifest", "candidate-selection audit"),
            "Configuration review is still a human responsibility.",
        ),
        _threat(
            "threat-source-edit",
            "asset-source",
            "Elevation of privilege",
            "T1195.001",
            "Source changes could bypass the thin-script and no-generated-code boundary.",
            ("project tests", "Ruff and mypy gates", "thin-orchestrator validation"),
            "The default run does not perform full static application security testing.",
        ),
        _threat(
            "threat-output-tamper",
            "asset-generated",
            "Repudiation",
            "T1195.002",
            "Generated reports or figures could be edited after analysis but before rendering.",
            ("artifact manifest checksums", "integrity attestation", "variable provenance sidecar"),
            "Local checksum evidence is not externally signed.",
        ),
        _threat(
            "threat-manuscript-injection",
            "asset-hydration",
            "Information disclosure",
            "T1195.002",
            "Manual prose could hard-code run facts that bypass validated variables.",
            ("strict manuscript source guard", "variable provenance", "figure registry"),
            "Stable scholarly prose and citekeys remain manually authored.",
        ),
        _threat(
            "threat-self-approval",
            "asset-review",
            "Spoofing",
            "T1195",
            "Generated review packets could be mistaken for human publication approval.",
            ("deferred review decisions", "publication_approved false", "review-gate validation"),
            "Publication remains outside the automated loop.",
        ),
        _threat(
            "threat-build-assumption",
            "asset-ci",
            "Denial of service",
            "T1195.003",
            "A local or CI build context could omit checks or run stale generated artifacts.",
            ("declared pipeline gates", "required artifact checks", "render validation"),
            "The exemplar does not sign build logs or isolate runners.",
        ),
    ]
    controls = [
        _control("ctrl-offline", "Default offline execution", "NIST_SP_800_207", "network_policy", "implemented"),
        _control(
            "ctrl-budget", "Zero LLM calls and zero cost budget", "NIST_SP_800_218_SSDF", "run_ledger", "implemented"
        ),
        _control("ctrl-hashes", "SHA-256 artifact checksums", "SLSA_SPEC", "integrity_attestation", "implemented"),
        _control("ctrl-inventory", "SBOM-style local inventory", "SLSA_SPEC", "supply_chain_inventory", "implemented"),
        _control(
            "ctrl-review", "Deferred human review gates", "NIST_SP_800_218_SSDF", "review_decisions", "implemented"
        ),
        _control("ctrl-allowlist", "Edit allowlist for proposals", "MITRE_ATTACK_T1195", "idea_ledger", "implemented"),
        _control(
            "ctrl-boundary",
            "Explicit non-claims in manuscript variables",
            "NIST_SP_800_207",
            "security_profile",
            "implemented",
        ),
    ]
    return {
        "schema": "template-autoresearch-threat-model-v1",
        "generated_at": generated_at,
        "frameworks": frameworks,
        "assets": assets,
        "threats": threats,
        "controls": controls,
        "summary": {
            "asset_count": len(assets),
            "threat_count": len(threats),
            "control_count": len(controls),
            "claim_boundary": "Threat model scopes local artifact integrity, not production deployment security.",
        },
    }


def supply_chain_inventory_payload(
    project_root: Path,
    output_paths: list[Path],
    *,
    generated_at: str,
) -> dict[str, object]:
    """Return an SBOM-style local inventory of inputs and generated artifacts."""
    input_paths = (
        ("root_pyproject", project_root.parents[1] / "pyproject.toml", False),
        ("root_uv_lock", project_root.parents[1] / "uv.lock", False),
        ("project_pyproject", project_root / "pyproject.toml", False),
        ("project_uv_lock", project_root / "uv.lock", False),
        ("autoresearch_config", project_root / "autoresearch.yaml", True),
        ("domain_profile", project_root / "domain_profile.yaml", True),
        ("experiment_plan", project_root / "experiment_plan.yaml", True),
        ("program", project_root / "program.md", True),
        ("seed_ideas", project_root / "seed_ideas.yaml", True),
        ("mnist_task", project_root / "mnist_task.yaml", True),
        ("mnist_fixture", project_root / "data" / "mnist_small.npz", True),
        ("mnist_provenance", project_root / "data" / "mnist_small_provenance.json", True),
        ("manuscript_config", project_root / "manuscript" / "config.yaml", True),
    )
    generated_paths = [
        path
        for path in sorted({path.resolve() for path in output_paths if path.exists()})
        if _project_relative_path(project_root, path) not in SECURITY_ARTIFACTS
    ]
    return {
        "schema": "template-autoresearch-supply-chain-inventory-v1",
        "generated_at": generated_at,
        "inventory_type": "SBOM-style local dependency and artifact inventory",
        "formal_sbom": False,
        "external_signing": False,
        "algorithm": "sha256",
        "inputs": [
            _file_record(project_root, identifier, path, required=required)
            for identifier, path, required in input_paths
        ],
        "generated_artifacts": [
            _file_record(project_root, f"generated-{index:03d}", path, required=True)
            for index, path in enumerate(generated_paths, start=1)
        ],
        "claim_boundary": "Inventory is local checksum metadata and does not claim SPDX, CycloneDX, or SLSA provenance.",
    }


def integrity_attestation_payload(
    project_root: Path,
    inventory: dict[str, object],
    *,
    generated_at: str,
) -> dict[str, object]:
    """Return checksum checks over required inventory entries."""
    checks: list[dict[str, object]] = []
    missing_count = 0
    mismatch_count = 0
    checked_count = 0
    for row in _inventory_rows(inventory):
        if not bool(row.get("required", True)):
            continue
        path_text = str(row.get("path", ""))
        path = project_root / path_text
        expected = str(row.get("sha256", ""))
        if not path.exists():
            status = "missing"
            actual = ""
            missing_count += 1
        else:
            actual = compute_sha256(path)
            status = "passed" if actual == expected else "mismatch"
            checked_count += 1
            mismatch_count += 0 if status == "passed" else 1
        checks.append(
            {
                "path": path_text,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": status,
            }
        )
    return {
        "schema": "template-autoresearch-integrity-attestation-v1",
        "generated_at": generated_at,
        "algorithm": "sha256",
        "status": "passed" if missing_count == 0 and mismatch_count == 0 else "failed",
        "checked_count": checked_count,
        "missing_count": missing_count,
        "mismatch_count": mismatch_count,
        "external_signature": False,
        "local_attestation": True,
        "checks": checks,
        "claim_boundary": "Checksums attest local files observed by this run; they are not externally signed provenance.",
    }


def render_security_review_markdown(
    profile: dict[str, object],
    threat_model: dict[str, object],
    inventory: dict[str, object],
    attestation: dict[str, object],
) -> str:
    """Render the generated security review packet."""
    summary = _mapping(threat_model.get("summary"))
    lines = [
        "# AutoResearch Security Review",
        "",
        "## Scope",
        "",
        f"- Mode: `{profile.get('mode')}`",
        f"- Network policy: `{profile.get('network_policy')}`",
        f"- Integrity algorithm: `{profile.get('integrity_algorithm')}`",
        f"- External signing: `{str(profile.get('external_signing')).lower()}`",
        f"- Claim scope: {profile.get('claim_scope')}",
        "",
        "## Threat Model Summary",
        "",
        f"- Assets: `{summary.get('asset_count')}`",
        f"- Threats: `{summary.get('threat_count')}`",
        f"- Controls: `{summary.get('control_count')}`",
        "",
        "## Integrity Attestation",
        "",
        f"- Status: `{attestation.get('status')}`",
        f"- Checked files: `{attestation.get('checked_count')}`",
        f"- Missing files: `{attestation.get('missing_count')}`",
        f"- Checksum mismatches: `{attestation.get('mismatch_count')}`",
        "- External signature: `false`",
        "",
        "## Inventory Summary",
        "",
        f"- Input records: `{len(_mapping_list(inventory.get('inputs')))}`",
        f"- Generated artifact records: `{len(_mapping_list(inventory.get('generated_artifacts')))}`",
        "",
        "## Non-Claims",
        "",
    ]
    non_claims = profile.get("non_claims", [])
    if not isinstance(non_claims, list):
        non_claims = []
    lines.extend(f"- {item}" for item in non_claims if isinstance(item, str))
    lines.extend(
        (
            "",
            "## Review Prompt",
            "",
            "A human reviewer should confirm that the local checksum, inventory, and threat-model "
            "evidence is sufficient for the manuscript's limited security claims before publication.",
            "",
        )
    )
    return "\n".join(lines)


def _asset(identifier: str, name: str, path: str, category: str) -> dict[str, str]:
    return {"id": identifier, "name": name, "path": path, "category": category}


def _threat(
    identifier: str,
    asset_id: str,
    stride: str,
    attack_technique: str,
    scenario: str,
    controls: tuple[str, ...],
    residual_risk: str,
) -> dict[str, object]:
    return {
        "id": identifier,
        "asset_id": asset_id,
        "stride_category": stride,
        "attack_technique": attack_technique,
        "scenario": scenario,
        "controls": list(controls),
        "residual_risk": residual_risk,
    }


def _control(
    identifier: str,
    name: str,
    framework: str,
    evidence_key: str,
    status: str,
) -> dict[str, str]:
    return {
        "id": identifier,
        "name": name,
        "framework": framework,
        "evidence_key": evidence_key,
        "status": status,
    }


def _file_record(
    project_root: Path,
    identifier: str,
    path: Path,
    *,
    required: bool,
) -> dict[str, object]:
    return {
        "id": identifier,
        "path": _project_relative_path(project_root, path),
        "required": required,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": compute_sha256(path) if path.exists() else "",
    }


def _inventory_rows(inventory: dict[str, object]) -> list[dict[str, Any]]:
    return [*_mapping_list(inventory.get("inputs")), *_mapping_list(inventory.get("generated_artifacts"))]


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _project_relative_path(project_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
