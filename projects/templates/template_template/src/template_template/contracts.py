"""Typed receipts for self-referential metrics and figure contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

METRICS_SCHEMA_VERSION = "template-template/metrics/1"
METRICS_RECEIPT_SCHEMA_VERSION = "template-template/metrics-receipt/1"
MATRIX_SCHEMA_VERSION = "template-template/comparative-matrix/1"
STEGANOGRAPHY_RECEIPT_SCHEMA_VERSION = "template-template/steganography-defaults/1"


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def validate_metrics_payload(metrics: dict[str, Any]) -> None:
    """Validate the stable envelope without constraining dynamic metric keys."""
    if metrics.get("metrics_schema_version") != METRICS_SCHEMA_VERSION:
        raise ValueError("metrics payload has unsupported or missing schema version")
    for key in ("generated_at", "public_exemplar_list"):
        if not isinstance(metrics.get(key), str) or not metrics[key].strip():
            raise ValueError(f"metrics payload requires non-empty {key}")
    for key in ("module_count", "project_count", "infra_test_count"):
        value = metrics.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"metrics payload requires positive integer {key}")


def build_metrics_receipt(metrics: dict[str, Any]) -> dict[str, object]:
    """Return a deterministic digest receipt for a generated metrics payload."""
    validate_metrics_payload(metrics)
    return {
        "schema_version": METRICS_RECEIPT_SCHEMA_VERSION,
        "metrics_schema_version": METRICS_SCHEMA_VERSION,
        "metrics_sha256": hashlib.sha256(_canonical(metrics)).hexdigest(),
        "public_exemplar_count": metrics["public_exemplar_list"].count("`") // 2,
    }


def validate_metrics_receipt(metrics: dict[str, Any], receipt: dict[str, Any]) -> None:
    expected = build_metrics_receipt(metrics)
    if receipt != expected:
        raise ValueError("metrics receipt is stale or schema-incompatible")


def validate_comparative_matrix_lockstep(manuscript_path: Path) -> dict[str, object]:
    """Check that the manuscript appendix has the same matrix axes and size."""
    from .figure_comparative_matrix import comparative_feature_matrix_data

    data, tools, capabilities = comparative_feature_matrix_data()
    if data.shape != (len(capabilities), len(tools)):
        raise ValueError("comparative matrix data shape does not match declared axes")
    text = manuscript_path.read_text(encoding="utf-8")
    missing = [capability for capability in capabilities if f"| {capability} |" not in text]
    if missing:
        raise ValueError(f"comparative matrix manuscript is missing rows: {missing}")
    if "| Container support | ~ |" not in text or float(data[11, 0]) != 0.5:
        raise ValueError("container partial-support marker is out of lockstep")
    return {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "rows": len(capabilities),
        "columns": len(tools),
        "missing_rows": tuple(missing),
        "status": "pass",
    }


def build_steganography_defaults_receipt(config_path: Path) -> dict[str, object]:
    """Digest the executable steganography defaults used by the manuscript."""
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    section = payload.get("steganography")
    if not isinstance(section, dict):
        raise ValueError("steganography config section is missing")
    keys = ("overlay_mode", "overlay_text", "overlay_opacity", "hashing_enabled", "barcodes_enabled")
    values = {key: section.get(key) for key in keys}
    if any(value is None for value in values.values()):
        raise ValueError("steganography defaults are incomplete")
    return {
        "schema_version": STEGANOGRAPHY_RECEIPT_SCHEMA_VERSION,
        "config_path": config_path.name,
        "defaults_sha256": hashlib.sha256(_canonical(values)).hexdigest(),
        "defaults": values,
    }


def validate_steganography_defaults_receipt(config_path: Path, receipt: dict[str, object]) -> None:
    if receipt != build_steganography_defaults_receipt(config_path):
        raise ValueError("steganography defaults receipt is stale")


__all__ = [
    "MATRIX_SCHEMA_VERSION",
    "METRICS_RECEIPT_SCHEMA_VERSION",
    "METRICS_SCHEMA_VERSION",
    "STEGANOGRAPHY_RECEIPT_SCHEMA_VERSION",
    "build_metrics_receipt",
    "build_steganography_defaults_receipt",
    "validate_comparative_matrix_lockstep",
    "validate_metrics_payload",
    "validate_metrics_receipt",
    "validate_steganography_defaults_receipt",
]
