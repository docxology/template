"""Claim-ledger validation against sheaf coverage artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_structured(path: Path) -> Any:
    if path.suffix in {".json", ".jsonl"}:
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return path.read_text(encoding="utf-8")


def _lookup_field(data: Any, field: str) -> Any:
    value = data
    for part in field.split("."):
        if isinstance(value, dict):
            value = value[part]
        elif isinstance(value, list):
            value = value[int(part)]
        else:
            raise KeyError(field)
    return value


def _numbers_equal(left: Any, right: Any, tolerance: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) is bool(right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tolerance
    return bool(left == right)


def _predicate_holds(value: Any, predicate: str) -> bool:
    if predicate == "exists":
        return value is not None
    if predicate == "file_exists":
        return bool(value)
    if predicate == "truthy":
        return bool(value)
    if predicate == "non_empty":
        return bool(value)
    if predicate == "zero":
        return float(value) == 0.0
    if predicate == "positive":
        return float(value) > 0.0
    if predicate == "all_true":
        if isinstance(value, dict):
            return all(bool(v) for v in value.values())
        if isinstance(value, list):
            return all(bool(v) for v in value)
    if predicate == "is_true":
        return value is True
    return False


def _set_equals(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list):
        return False
    return {str(item) for item in left} == {str(item) for item in right}


def _evidence_spec_holds(value: Any, evidence: dict[str, Any]) -> bool:
    if "field" in evidence:
        try:
            value = _lookup_field(value, str(evidence["field"]))
        except (KeyError, TypeError, ValueError, IndexError):
            return False
    tolerance = float(evidence.get("tolerance", 0.0))
    if "equals" in evidence and not _numbers_equal(value, evidence["equals"], tolerance):
        return False
    if "approx" in evidence and not _numbers_equal(value, evidence["approx"], tolerance):
        return False
    if "min" in evidence and float(value) < float(evidence["min"]):
        return False
    if "max" in evidence and float(value) > float(evidence["max"]):
        return False
    if "contains" in evidence and evidence["contains"] not in value:
        return False
    if "set_equals" in evidence and not _set_equals(value, evidence["set_equals"]):
        return False
    if "len_equals" in evidence and len(value) != int(evidence["len_equals"]):
        return False
    if "len_min" in evidence and len(value) < int(evidence["len_min"]):
        return False
    if "all" in evidence:
        nested = evidence["all"]
        if not isinstance(value, list) or not isinstance(nested, dict):
            return False
        if not all(_evidence_spec_holds(item, nested) for item in value):
            return False
    if "any" in evidence:
        nested = evidence["any"]
        if not isinstance(value, list) or not isinstance(nested, dict):
            return False
        if not any(_evidence_spec_holds(item, nested) for item in value):
            return False
    predicate = evidence.get("predicate")
    if predicate and not _predicate_holds(value, str(predicate)):
        return False
    return True


def _evidence_predicate_name(evidence: dict[str, Any]) -> str:
    if evidence.get("predicate"):
        return str(evidence["predicate"])
    for key in ("equals", "approx", "min", "max", "contains", "set_equals", "len_equals", "len_min", "all", "any"):
        if key in evidence:
            return key
    return ""


def claim_evidence_status_rows(
    project_root: Path,
    *,
    ledger_path: Path | None = None,
    allow_missing_certificate: bool = False,
) -> list[dict[str, Any]]:
    """Return row-level resolution status for every claim-ledger evidence declaration."""
    root = project_root.resolve()
    path = ledger_path or root / "data" / "claim_ledger.yaml"
    if not path.exists():
        return []
    import yaml

    ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows: list[dict[str, Any]] = []
    for claim in ledger.get("claims") or []:
        claim_id = str(claim.get("id") or "<unknown>")
        rel = str(claim.get("path") or "")
        evidence = claim.get("evidence") if isinstance(claim.get("evidence"), dict) else {}
        predicate = _evidence_predicate_name(evidence)
        waiver = str(evidence.get("waiver") or "")
        field = str(evidence.get("field") or evidence.get("jsonpath") or "")
        artifact = root / rel if rel else root
        artifact_exists = bool(rel) and artifact.exists()
        self_referential_audit = (
            claim_id == "claim_evidence_audit_typed"
            and rel == "output/reports/claim_evidence_audit.json"
            and field in {"all_complete", "all_claims_typed"}
        )
        fixed_point_deferred = allow_missing_certificate and rel == "output/data/sheaf_gluing_certificate.json"
        has_tracks = bool(claim.get("tracks"))
        has_evidence = bool(evidence)
        substantive = bool(has_evidence and (predicate or waiver))
        evidence_resolved = False
        evidence_holds = False
        failure_reason = ""
        if not rel:
            failure_reason = "missing path"
        elif self_referential_audit:
            artifact_exists = True
            evidence_resolved = True
            evidence_holds = True
        elif fixed_point_deferred:
            artifact_exists = True
            evidence_resolved = True
            evidence_holds = True
        elif not artifact_exists:
            failure_reason = f"missing artifact {rel}"
        elif not has_evidence:
            failure_reason = "missing evidence"
        elif waiver:
            evidence_resolved = True
            evidence_holds = True
        else:
            if evidence.get("predicate") == "file_exists":
                value: Any = artifact_exists
                spec = {key: val for key, val in evidence.items() if key != "field"}
            else:
                try:
                    value = _load_structured(artifact)
                    spec = evidence
                    evidence_resolved = True
                except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
                    failure_reason = f"cannot load evidence from {rel}: {exc}"
                    value = None
                    spec = {}
            if not evidence_resolved and evidence.get("predicate") == "file_exists":
                evidence_resolved = True
            if evidence_resolved:
                try:
                    evidence_holds = _evidence_spec_holds(value, spec)
                except (TypeError, ValueError, KeyError, IndexError):
                    evidence_holds = False
                if not evidence_holds:
                    failure_reason = f"evidence predicate failed for {rel}"
        if not has_tracks:
            failure_reason = failure_reason or "tracks must not be empty"
        complete = (
            has_evidence
            and has_tracks
            and substantive
            and artifact_exists
            and evidence_resolved
            and evidence_holds
            and not failure_reason
        )
        rows.append(
            {
                "id": claim_id,
                "path": rel,
                "jsonpath": f"$.{field}" if field else "$",
                "predicate": predicate,
                "waiver": waiver,
                "has_evidence": has_evidence,
                "has_tracks": has_tracks,
                "substantive": substantive,
                "artifact_exists": artifact_exists,
                "evidence_resolved": evidence_resolved,
                "evidence_holds": evidence_holds,
                "self_referential_audit": self_referential_audit,
                "fixed_point_deferred": fixed_point_deferred,
                "complete": complete,
                "failure_reason": "" if complete else failure_reason or "missing predicate/waiver or tracks",
            }
        )
    return rows


def typed_claim_evidence_issues(
    project_root: Path,
    *,
    ledger_path: Path | None = None,
    allow_missing_certificate: bool = False,
) -> list[str]:
    """Return explicit typed-evidence failures for ``claim_ledger.yaml``."""
    root = project_root.resolve()
    path = ledger_path or root / "data" / "claim_ledger.yaml"
    if not path.exists():
        return [f"claim ledger missing: {path}"]
    import yaml

    ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    issues: list[str] = []
    for claim in ledger.get("claims") or []:
        claim_id = str(claim.get("id") or "<unknown>")
        rel = claim.get("path")
        if not rel:
            issues.append(f"{claim_id}: missing path")
            continue
        if allow_missing_certificate and str(rel) == "output/data/sheaf_gluing_certificate.json":
            continue
        artifact = root / str(rel)
        if not artifact.exists():
            issues.append(f"{claim_id}: missing artifact {rel}")
            continue
        evidence = claim.get("evidence")
        if evidence:
            if evidence.get("predicate") == "file_exists":
                value: Any = artifact.exists()
                spec = {k: v for k, v in evidence.items() if k != "field"}
            else:
                try:
                    value = _load_structured(artifact)
                    spec = evidence
                except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
                    issues.append(f"{claim_id}: cannot load evidence from {rel}: {exc}")
                    continue
            if not _evidence_spec_holds(value, spec):
                issues.append(f"{claim_id}: evidence predicate failed for {rel}")
        if "tracks" in claim and not claim.get("tracks"):
            issues.append(f"{claim_id}: tracks must not be empty")
    return issues


def validate_typed_claim_evidence(
    project_root: Path,
    *,
    ledger_path: Path | None = None,
    allow_missing_certificate: bool = False,
) -> bool:
    """Validate optional typed evidence declarations in ``claim_ledger.yaml``."""
    return not typed_claim_evidence_issues(
        project_root,
        ledger_path=ledger_path,
        allow_missing_certificate=allow_missing_certificate,
    )


def validate_claim_ledger(project_root: Path) -> bool:
    """Validate claim ledger."""
    root = project_root.resolve()
    ledger_path = root / "data" / "claim_ledger.yaml"
    if not ledger_path.exists():
        return False
    import yaml

    from manuscript.sheaf import (
        gray_cell_count_from_json,
        load_coverage_json,
        load_manifest,
        load_track_registry,
        validate_coverage_json_data,
    )

    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8")) or {}
    manifest_path = root / "manuscript" / "sheaf" / "manifest.yaml"
    manifest = load_manifest(manifest_path, project_root=root) if manifest_path.exists() else None
    registry = (
        load_track_registry(root / manifest.registry_path)
        if manifest and (root / manifest.registry_path).exists()
        else None
    )
    json_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    coverage_data = load_coverage_json(json_path) if json_path.exists() else None

    for claim in ledger.get("claims") or []:
        rel = claim.get("path")
        if rel and not (root / str(rel)).exists():
            return False
        claim_id = claim.get("id")
        if claim_id == "coverage_no_gray":
            if coverage_data is None or manifest is None or registry is None:
                return False
            if gray_cell_count_from_json(coverage_data) > 0:
                return False
            json_issues = validate_coverage_json_data(coverage_data, manifest, registry)
            if any(i.level == "error" for i in json_issues):
                return False
    return validate_typed_claim_evidence(root, ledger_path=ledger_path)


def verify_claim_bindings(project_root: Path) -> list[str]:
    """Semantic claim bindings -- tie manuscript values/adjectives to their oracles."""
    import json

    import yaml as _yaml

    root = project_root.resolve()
    violations: list[str] = []

    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    summary_mode: str | None = None
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            violations.append(f"si_tmaze_summary.json unreadable: {exc}")
            summary = {}
        steps = summary.get("steps")
        summary_mode = summary.get("mode")
        if not isinstance(steps, int) or steps <= 0:
            violations.append(f"si_tmaze_summary.steps must be a positive measured count, got {steps!r}")
        if summary_mode not in {"state_inference", "policy_inference"}:
            violations.append(f"si_tmaze_summary.mode invalid: {summary_mode!r}")

    cfg_path = root / "pymdp.yaml"
    if cfg_path.is_file() and summary_mode is not None:
        try:
            cfg = _yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except (OSError, _yaml.YAMLError) as exc:
            cfg = {}
            violations.append(f"pymdp.yaml unreadable: {exc}")
        cfg_mode = cfg.get("mode")
        if cfg_mode is None:
            violations.append("pymdp.yaml is missing the mandatory 'mode' key (mode-match bind disarmed)")
        elif cfg_mode != summary_mode:
            violations.append(
                f"pymdp mode mismatch: config mode={cfg_mode!r} but recorded rollout mode={summary_mode!r}"
            )

    invariants_section = root / "manuscript" / "13_results_invariants.md"
    if invariants_section.is_file() and "merged" in invariants_section.read_text(encoding="utf-8").lower():
        from manuscript.invariant_counts import invariants_are_merged

        if not invariants_are_merged(root):
            violations.append(
                "section 13 claims a merged analytical+simulation report, but no "
                "simulation invariants are present under output/reports/"
            )

    return violations
