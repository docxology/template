"""Dry-run and explicit-boundary tests for the release rehearsal."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.publishing.rehearsal import build_clean_checkout_plan


def test_rehearsal_plan_is_offline_and_skipped_by_default() -> None:
    root = Path(__file__).resolve().parents[3]
    plan = build_clean_checkout_plan(root)
    assert plan.network_allowed is False
    assert plan.runs == 2
    assert plan.status == "skipped"
    assert "--execute" in plan.skip_reason


def test_rehearsal_plan_rejects_empty_commands(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_clean_checkout_plan(tmp_path, commands=())
