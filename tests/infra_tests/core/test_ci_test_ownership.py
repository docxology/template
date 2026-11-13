"""Unowned reporting source changes retain complete-package test selection."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.testing.ci_infra import infrastructure_files
from infrastructure.core.testing.ci_test_ownership import SOURCE_TEST_OWNERS

ROOT = Path(__file__).resolve().parents[3]


def test_unowned_reporting_helper_still_selects_complete_package_fallback() -> None:
    source = "infrastructure/reporting/a_genuinely_unowned_new_protocol_helper.py"
    assert source not in SOURCE_TEST_OWNERS
    expected = set(infrastructure_files(ROOT)) | {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "tests/infra_tests/reporting").rglob("test_*.py")
    }
    assert set(infrastructure_files(ROOT, (source,))) == expected
