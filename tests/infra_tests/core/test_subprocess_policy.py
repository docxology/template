"""Behavioral tests for the shared intentional-subprocess policy boundary."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from infrastructure.core.subprocess_policy import (
    INTENTIONAL_SUBPROCESS_POLICIES,
    SubprocessPolicy,
    SubprocessPolicyError,
    run_with_policy,
    validate_policy_inventory,
)


def test_checked_policy_uses_real_process_and_reports_failure(tmp_path: Path) -> None:
    policy = SubprocessPolicy(
        policy_id="fixture-check",
        source_path="infrastructure/core/subprocess_policy.py",
        timeout_seconds=5,
        check=True,
    )
    with pytest.raises(SubprocessPolicyError, match="fixture-check"):
        run_with_policy(
            (sys.executable, "-c", "raise SystemExit(7)"),
            cwd=tmp_path,
            env={"PATH": "/usr/bin:/bin"},
            policy=policy,
        )


def test_policy_timeout_kills_descendants(tmp_path: Path) -> None:
    marker = tmp_path / "leaked.txt"
    child = f"import pathlib,time; time.sleep(2); pathlib.Path({str(marker)!r}).write_text('leaked')"
    parent = f"import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(30)"
    policy = SubprocessPolicy(
        policy_id="timeout-fixture",
        source_path="infrastructure/core/subprocess_policy.py",
        timeout_seconds=1,
    )
    result = run_with_policy(
        (sys.executable, "-c", parent),
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin"},
        policy=policy,
    )
    assert result.timed_out is True
    assert result.returncode != 0
    import time

    time.sleep(2.2)
    assert not marker.exists()


def test_policy_inventory_has_unique_existing_sources(tmp_path: Path) -> None:
    del tmp_path
    root = Path(__file__).resolve().parents[3]
    assert validate_policy_inventory(INTENTIONAL_SUBPROCESS_POLICIES, root) == []


def test_policy_inventory_rejects_missing_source_and_no_process_group(tmp_path: Path) -> None:
    bad = SubprocessPolicy(
        policy_id="bad",
        source_path="missing.py",
        timeout_seconds=0,
        process_group=False,
    )
    errors = validate_policy_inventory((bad,), tmp_path)
    assert any(error.startswith("INVALID-POLICY:") for error in errors)
