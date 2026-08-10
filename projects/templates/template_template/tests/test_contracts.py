"""Schema, lockstep, and deterministic-default controls for the meta-template."""

from __future__ import annotations

from pathlib import Path

import pytest

from template_template.contracts import (
    build_metrics_receipt,
    build_steganography_defaults_receipt,
    validate_comparative_matrix_lockstep,
    validate_metrics_receipt,
    validate_steganography_defaults_receipt,
)
from template_template.metrics import build_manuscript_metrics_dict

from helpers import PROJECT_DIR, REPO_ROOT


def test_metrics_receipt_is_deterministic_and_rejects_stale_payload() -> None:
    metrics = build_manuscript_metrics_dict(REPO_ROOT)
    receipt = build_metrics_receipt(metrics)
    validate_metrics_receipt(metrics, receipt)
    changed = dict(metrics)
    changed["module_count"] = int(changed["module_count"]) + 1
    with pytest.raises(ValueError, match="stale"):
        validate_metrics_receipt(changed, receipt)


def test_comparative_matrix_is_lockstep_with_manuscript() -> None:
    result = validate_comparative_matrix_lockstep(PROJECT_DIR / "manuscript" / "08f_appendix_matrix.md")
    assert result["status"] == "pass"
    assert result["rows"] == 14
    assert result["columns"] == 10


def test_comparative_matrix_missing_row_is_rejected(tmp_path: Path) -> None:
    source = (PROJECT_DIR / "manuscript" / "08f_appendix_matrix.md").read_text(encoding="utf-8")
    path = tmp_path / "matrix.md"
    path.write_text(source.replace("| Testing enforcement |", "| Removed row |"), encoding="utf-8")
    with pytest.raises(ValueError, match="missing rows"):
        validate_comparative_matrix_lockstep(path)


def test_steganography_defaults_receipt_detects_default_drift(tmp_path: Path) -> None:
    config = tmp_path / "secure.yaml"
    config.write_text(
        "steganography:\n  overlay_mode: text\n  overlay_text: CONFIDENTIAL\n"
        "  overlay_opacity: 0.08\n  hashing_enabled: true\n  barcodes_enabled: true\n",
        encoding="utf-8",
    )
    receipt = build_steganography_defaults_receipt(config)
    validate_steganography_defaults_receipt(config, receipt)
    config.write_text(config.read_text(encoding="utf-8").replace("0.08", "0.09"), encoding="utf-8")
    with pytest.raises(ValueError, match="stale"):
        validate_steganography_defaults_receipt(config, receipt)
