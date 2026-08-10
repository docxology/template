"""Public-scope claim-binding inventory tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from infrastructure.validation.claims import build_claim_binding_receipt, validate_claim_bindings


def test_public_claim_binding_inventory_is_complete() -> None:
    root = Path(__file__).resolve().parents[3]
    report = validate_claim_bindings(root)
    assert report.errors == ()
    assert len(report.projects) == 24
    assert any(record.state == "bound" for record in report.projects)
    assert any(record.state == "not_applicable" for record in report.projects)


def test_claim_binding_inventory_rejects_missing_roster_row(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    source = root / "tests/regression/claim_bindings.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["projects"] = payload["projects"][:-1]
    manifest = tmp_path / "claim_bindings.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = validate_claim_bindings(root, manifest)
    assert any("missing public claim-binding row" in error for error in report.errors)


def test_claim_binding_inventory_rejects_pin_producer_drift(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    source = root / "tests/regression/claim_bindings.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    target = next(row for row in payload["projects"] if row["state"] == "bound")
    pin_path = root / target["pin_file"]
    original = json.loads(pin_path.read_text(encoding="utf-8"))
    key = next(key for key in original if not key.startswith("_"))
    original[key]["verifier_function"] = ""

    pin_root = tmp_path / "tests/regression/pinned_values"
    pin_root.mkdir(parents=True)
    for candidate in (root / "tests/regression/pinned_values").glob("*.json"):
        shutil.copy2(candidate, pin_root / candidate.name)
    altered_pin = pin_root / pin_path.name
    altered_pin.write_text(json.dumps(original), encoding="utf-8")
    manifest = tmp_path / "claim_bindings.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    report = validate_claim_bindings(tmp_path, manifest)
    assert any("verifier_function" in error for error in report.errors)


def test_claim_binding_receipt_is_typed_and_digest_bound() -> None:
    root = Path(__file__).resolve().parents[3]
    receipt = build_claim_binding_receipt(validate_claim_bindings(root))
    assert receipt.validate() == []
    assert receipt.to_dict()["schema_version"] == "template-claim-binding-receipt/v1"
