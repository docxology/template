"""Negative controls for the regression-tier collection manifest."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
REGRESSION_ROOT = REPO_ROOT / "tests" / "regression"


def test_regression_manifest_names_every_claim_binding_test_file() -> None:
    manifest = json.loads((REGRESSION_ROOT / "manifest.json").read_text(encoding="utf-8"))
    expected = set(manifest["required_test_files"])
    actual = {path.relative_to(REGRESSION_ROOT).as_posix() for path in REGRESSION_ROOT.rglob("test_*.py")}
    assert actual == expected


def test_regression_manifest_has_nonzero_collection_floor() -> None:
    manifest = json.loads((REGRESSION_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["minimum_collected_tests"] >= 55
