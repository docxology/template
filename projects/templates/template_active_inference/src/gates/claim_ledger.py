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
        if claim_id == "coverage_no_gray" and coverage_data is not None:
            if gray_cell_count_from_json(coverage_data) > 0:
                return False
            if manifest is not None and registry is not None:
                json_issues = validate_coverage_json_data(coverage_data, manifest, registry)
                if any(i.level == "error" for i in json_issues):
                    return False
    return True
