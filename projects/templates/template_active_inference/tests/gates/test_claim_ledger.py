"""Claim ledger gate negative controls."""

from __future__ import annotations

from pathlib import Path

from gates.validation import validate_manuscript


def test_validate_manuscript_claim_ledger_missing_file_negative(project_root: Path, tmp_path: Path) -> None:
    ledger = project_root / "data" / "claim_ledger.yaml"
    backup = tmp_path / "claim_ledger.yaml.bak"
    backup.write_text(ledger.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        ledger.unlink()
        checks = validate_manuscript(project_root)
        assert checks["claim_ledger_valid"] is False
    finally:
        ledger.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")


def test_validate_manuscript_claim_ledger_negative(project_root: Path) -> None:
    target = project_root / "output" / "figures" / "sheaf_layers_overview.png"
    backup_exists = target.is_file()
    backup_bytes = target.read_bytes() if backup_exists else b""
    try:
        if backup_exists:
            target.unlink()
        checks = validate_manuscript(project_root)
        assert checks["claim_ledger_valid"] is False
    finally:
        if backup_exists:
            target.write_bytes(backup_bytes)
