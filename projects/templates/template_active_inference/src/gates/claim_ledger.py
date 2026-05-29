"""Claim-ledger validation against sheaf coverage artifacts."""

from __future__ import annotations

from pathlib import Path


def validate_claim_ledger(project_root: Path) -> bool:
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
    return True


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
