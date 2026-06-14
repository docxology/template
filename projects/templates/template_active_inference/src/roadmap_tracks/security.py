"""Deterministic security-posture audit for the public exemplar."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SECURITY_POSTURE_SCHEMA = "template_active_inference.security_posture_audit.v1"

SOURCE_SENTINEL = "project_source_tree"
SCAN_ROOTS = ("src", "scripts", "tests", "manuscript", "data", "lean", "gnn")
SCAN_FILES = ("pyproject.toml", "tracks.yaml", "figures.yaml", "pymdp.yaml", "manuscript/config.yaml")
SCAN_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".lean", ".json"}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{36,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----")),
    (
        "long_lived_secret_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret[_-]?access[_-]?key|private[_-]?key)\b"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{20,}"
        ),
    ),
)

SECURITY_CONTROLS: tuple[dict[str, Any], ...] = (
    {
        "control_id": "public_data_boundary",
        "pillar": "data_protection",
        "status": "enforced",
        "threat_model": "private or restricted data enters a public release artifact",
        "attack_tactic": "collection",
        "evidence_artifacts": (
            "output/reports/blocked_scope_manifest.json",
            "output/reports/scope_boundary_audit.json",
        ),
        "validators": (
            "validate_outputs.blocked_scope_manifest_schema",
            "validate_outputs.scope_boundary_audit_schema",
        ),
        "boundary": "public toy-only exemplar; private, restricted, empirical, network, and LLM evidence are blocked",
        "negative_control_id": "private_data_manifest_live",
        "mitigation": "blocked-scope rows must stay non-live until provenance and privacy gates exist",
    },
    {
        "control_id": "offline_reproducibility",
        "pillar": "supply_chain_integrity",
        "status": "enforced",
        "threat_model": "network-dependent research or runtime fetch changes the published evidence",
        "attack_tactic": "supply_chain_compromise",
        "evidence_artifacts": (
            "output/reports/reproducibility_replay.json",
            "output/reports/replay_matrix.json",
        ),
        "validators": (
            "validate_outputs.reproducibility_replay_schema",
            "validate_outputs.replay_matrix_schema",
        ),
        "boundary": "core evidence is generated from local deterministic artifacts rather than live network calls",
        "negative_control_id": "network_research_claim_without_replay",
        "mitigation": "network-derived research remains blocked until an offline replay manifest is promoted",
    },
    {
        "control_id": "artifact_hash_integrity",
        "pillar": "artifact_integrity",
        "status": "enforced",
        "threat_model": "post-generation artifact drift is published without detection",
        "attack_tactic": "tampering",
        "evidence_artifacts": (
            "output/data/artifact_provenance.json",
            "output/reports/artifact_diffoscope.json",
            "output/reports/figure_hash_manifest.json",
        ),
        "validators": (
            "validate_outputs.artifact_provenance_schema",
            "validate_outputs.artifact_diffoscope_schema",
            "validate_outputs.figure_hash_manifest_schema",
        ),
        "boundary": "generated artifacts are hashed and diffed against live filesystem outputs",
        "negative_control_id": "artifact_hash_drift",
        "mitigation": "hash drift fails validation before release evidence can be cited",
    },
    {
        "control_id": "release_bundle_parity",
        "pillar": "release_integrity",
        "status": "enforced",
        "threat_model": "project-local and copied-root deliverables diverge",
        "attack_tactic": "tampering",
        "evidence_artifacts": (
            "output/reports/release_bundle_manifest.json",
            "output/reports/release_attestation.json",
        ),
        "validators": (
            "validate_outputs.release_bundle_manifest_schema",
            "validate_outputs.release_attestation_schema",
        ),
        "boundary": "release parity is checked locally; PDF and web outputs may defer until render/copy stages",
        "negative_control_id": "release_bundle_parity_failure",
        "mitigation": "copy parity and release attestation must be refreshed before publication delivery",
    },
    {
        "control_id": "claim_scope_traceability",
        "pillar": "evidence_integrity",
        "status": "enforced",
        "threat_model": "publication claim laundering through uncited or untyped evidence",
        "attack_tactic": "impact",
        "evidence_artifacts": (
            "output/data/evidence_field_index.json",
            "output/reports/claim_evidence_audit.json",
            "output/data/scholarship_source_matrix.json",
            "output/data/track_lane_matrix.json",
        ),
        "validators": (
            "validate_outputs.evidence_field_index_schema",
            "validate_outputs.claim_evidence_audit_schema",
            "validate_outputs.scholarship_source_matrix_schema",
            "validate_outputs.track_lane_matrix_schema",
        ),
        "boundary": "claims must map to typed fields, guarded source roles, and promotion rows",
        "negative_control_id": "claim_without_evidence_field",
        "mitigation": "claim ledger, scholarship rows, and track-lane rows must agree",
    },
    {
        "control_id": "formal_boundary",
        "pillar": "formal_integrity",
        "status": "enforced",
        "threat_model": "informal claims are mistaken for proved Lean obligations",
        "attack_tactic": "defense_evasion",
        "evidence_artifacts": (
            "output/reports/lean_theorem_inventory.json",
            "output/data/proof_extraction_index.json",
            "output/data/theorem_traceability_matrix.json",
        ),
        "validators": (
            "validate_outputs.lean_theorem_inventory_schema",
            "validate_outputs.proof_extraction_index_schema",
            "validate_outputs.theorem_traceability_matrix_schema",
        ),
        "boundary": "Lean-backed rows are explicit; non-proved boundaries stay outside empirical claims",
        "negative_control_id": "proof_extraction_missing_statement",
        "mitigation": "Lean inventory and proof extraction must remain constructive and linked",
    },
    {
        "control_id": "secret_pattern_absence",
        "pillar": "secret_hygiene",
        "status": "enforced",
        "threat_model": "long-lived credential or private key is committed to the public exemplar",
        "attack_tactic": "credential_access",
        "evidence_artifacts": (SOURCE_SENTINEL,),
        "validators": ("validate_outputs.security_posture_audit_schema",),
        "boundary": "tracked project source/config surfaces are scanned for high-risk credential patterns",
        "negative_control_id": "embedded_secret_pattern",
        "mitigation": "secret-pattern hits must be zero; findings report path and pattern only, not secret values",
    },
    {
        "control_id": "signed_release_attestation",
        "pillar": "slsa_attestation",
        "status": "deferred",
        "threat_model": "production release lacks signed provenance or SBOM attestation",
        "attack_tactic": "supply_chain_compromise",
        "evidence_artifacts": ("output/reports/release_attestation.json",),
        "validators": ("validate_outputs.release_attestation_schema",),
        "boundary": "the exemplar is a local public template; production Sigstore/cosign signing is not claimed",
        "negative_control_id": "unsigned_production_release_claim",
        "mitigation": "production adoption must add signed in-toto/SBOM provenance before deployment",
    },
    {
        "control_id": "zero_trust_runtime_boundary",
        "pillar": "zero_trust",
        "status": "deferred",
        "threat_model": "a manuscript reader infers production zero-trust runtime coverage from a static exemplar",
        "attack_tactic": "valid_accounts",
        "evidence_artifacts": (
            "tracks.yaml",
            "output/reports/blocked_scope_manifest.json",
        ),
        "validators": (
            "validate_manuscript.blocked_empirical_adapter",
            "validate_outputs.security_posture_audit_schema",
        ),
        "boundary": "no deployed service, identity plane, endpoint fleet, or production network is claimed",
        "negative_control_id": "production_zero_trust_claim_without_runtime",
        "mitigation": "production use must add identity, device posture, workload identity, logging, and IR gates",
    },
)


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _scan_paths(root: Path) -> list[Path]:
    paths: set[Path] = {root / rel for rel in SCAN_FILES}
    for rel_root in SCAN_ROOTS:
        base = root / rel_root
        if base.is_dir():
            paths.update(path for path in base.rglob("*") if path.is_file() and path.suffix in SCAN_SUFFIXES)
    return sorted(path for path in paths if path.is_file())


def _scan_secret_patterns(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in _scan_paths(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, 1):
            for pattern_id, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "path": path.relative_to(root).as_posix(),
                            "line": line_number,
                            "pattern_id": pattern_id,
                        }
                    )
    return findings


def _artifact_present(root: Path, rel: str) -> bool:
    if rel == SOURCE_SENTINEL:
        return any((root / scan_root).is_dir() for scan_root in SCAN_ROOTS)
    return (root / rel).exists()


def _control_row(root: Path, control: dict[str, Any], *, secret_finding_count: int) -> dict[str, Any]:
    artifacts = [str(artifact) for artifact in control["evidence_artifacts"]]
    validators = [str(validator) for validator in control["validators"]]
    evidence_present = all(_artifact_present(root, artifact) for artifact in artifacts)
    deferred_scoped = control["status"] == "enforced" or bool(control.get("boundary") and control.get("mitigation"))
    secret_ok = control["control_id"] != "secret_pattern_absence" or secret_finding_count == 0
    row = {
        **control,
        "evidence_artifacts": artifacts,
        "validators": validators,
        "evidence_present": evidence_present,
        "validator_bound": bool(validators),
        "boundary_declared": bool(str(control.get("boundary") or "").strip()),
        "negative_control_declared": bool(str(control.get("negative_control_id") or "").strip()),
        "deferred_scoped": deferred_scoped,
        "secret_findings_absent": secret_ok,
    }
    row["control_ok"] = (
        row["evidence_present"]
        and row["validator_bound"]
        and row["boundary_declared"]
        and row["negative_control_declared"]
        and row["deferred_scoped"]
        and row["secret_findings_absent"]
    )
    return row


def build_security_posture_audit(project_root: Path) -> dict[str, Any]:
    """Build the APT/supply-chain posture matrix from live local evidence."""
    root = project_root.resolve()
    secret_findings = _scan_secret_patterns(root)
    secret_finding_count = len(secret_findings)
    rows = [_control_row(root, control, secret_finding_count=secret_finding_count) for control in SECURITY_CONTROLS]
    enforced_rows = [row for row in rows if row["status"] == "enforced"]
    deferred_rows = [row for row in rows if row["status"] == "deferred"]
    high_risk_gap_count = sum(1 for row in rows if row["status"] == "enforced" and not row["control_ok"])
    return {
        "schema": SECURITY_POSTURE_SCHEMA,
        "rows": rows,
        "control_count": len(rows),
        "enforced_count": len(enforced_rows),
        "deferred_count": len(deferred_rows),
        "pillars": sorted({str(row["pillar"]) for row in rows}),
        "attack_tactics": sorted({str(row["attack_tactic"]) for row in rows}),
        "secret_scan": {
            "scan_root_count": len(SCAN_ROOTS),
            "file_count": len(_scan_paths(root)),
            "pattern_count": len(SECRET_PATTERNS),
            "findings": secret_findings,
        },
        "secret_finding_count": secret_finding_count,
        "high_risk_gap_count": high_risk_gap_count,
        "all_evidence_present": bool(rows) and all(row["evidence_present"] for row in rows),
        "all_validators_bound": bool(rows) and all(row["validator_bound"] for row in rows),
        "all_negative_controls_declared": bool(rows) and all(row["negative_control_declared"] for row in rows),
        "all_deferred_controls_scoped": bool(rows) and all(row["deferred_scoped"] for row in rows),
        "all_secret_patterns_absent": secret_finding_count == 0,
        "all_controls_ok": bool(rows) and all(row["control_ok"] for row in rows),
    }


def write_security_posture_audit(project_root: Path) -> Path:
    """Write the deterministic security posture audit report."""
    root = project_root.resolve()
    return _write_json(
        root / "output" / "reports" / "security_posture_audit.json",
        build_security_posture_audit(root),
    )


def _row_key(row: dict[str, Any]) -> str:
    return str(row.get("control_id") or "")


def validate_security_posture_audit(project_root: Path) -> list[str]:
    """Validate the saved security posture audit against live evidence."""
    root = project_root.resolve()
    path = root / "output" / "reports" / "security_posture_audit.json"
    if not path.is_file():
        return ["security_posture_audit.json missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return ["security_posture_audit.json is not valid JSON"]
    issues: list[str] = []
    if payload.get("schema") != SECURITY_POSTURE_SCHEMA:
        issues.append("security_posture_audit.json schema mismatch")
    expected = build_security_posture_audit(root)
    rows = payload.get("rows") or []
    saved_rows = {_row_key(row): row for row in rows}
    expected_rows = {_row_key(row): row for row in expected.get("rows") or []}
    if set(saved_rows) != set(expected_rows):
        issues.append("security_posture_audit.json control set disagrees with source controls")
    rederived_fields = (
        "status",
        "pillar",
        "attack_tactic",
        "evidence_artifacts",
        "validators",
        "evidence_present",
        "validator_bound",
        "boundary_declared",
        "negative_control_declared",
        "deferred_scoped",
        "secret_findings_absent",
        "control_ok",
    )
    for control_id, row in saved_rows.items():
        expected_row = expected_rows.get(control_id)
        if expected_row is None:
            continue
        if any(row.get(field) != expected_row.get(field) for field in rederived_fields):
            issues.append(f"security_posture_audit.json stale or forged row evidence for {control_id}")
            break
    rows_ok = bool(rows) and all(row.get("control_ok") for row in rows)
    evidence_ok = bool(rows) and all(row.get("evidence_present") for row in rows)
    validators_ok = bool(rows) and all(row.get("validator_bound") for row in rows)
    negatives_ok = bool(rows) and all(row.get("negative_control_declared") for row in rows)
    deferred_ok = bool(rows) and all(row.get("deferred_scoped") for row in rows)
    aggregate_checks = {
        "control_count": len(rows),
        "enforced_count": sum(1 for row in rows if row.get("status") == "enforced"),
        "deferred_count": sum(1 for row in rows if row.get("status") == "deferred"),
        "secret_finding_count": len((payload.get("secret_scan") or {}).get("findings") or []),
        "high_risk_gap_count": sum(
            1 for row in rows if row.get("status") == "enforced" and row.get("control_ok") is not True
        ),
        "all_controls_ok": rows_ok,
        "all_evidence_present": evidence_ok,
        "all_validators_bound": validators_ok,
        "all_negative_controls_declared": negatives_ok,
        "all_deferred_controls_scoped": deferred_ok,
        "all_secret_patterns_absent": len((payload.get("secret_scan") or {}).get("findings") or []) == 0,
    }
    for field, derived in aggregate_checks.items():
        if payload.get(field) != derived or payload.get(field) != expected.get(field):
            issues.append(f"security_posture_audit.json {field} disagrees with live evidence")
    if payload.get("all_controls_ok") is not True:
        issues.append("security_posture_audit.json has incomplete security controls")
    if payload.get("all_secret_patterns_absent") is not True:
        issues.append("security_posture_audit.json found high-risk secret patterns")
    return issues
