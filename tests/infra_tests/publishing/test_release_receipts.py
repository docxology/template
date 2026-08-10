"""Behavioral tests for versioned, authority-aware release receipts."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.subprocess_policy import SubprocessPolicyRecord
from infrastructure.publishing.release_receipts import (
    CleanCheckoutReceipt,
    CommandReceipt,
    CoverageGapSnapshot,
    ReleaseMetadataReceipt,
    SubprocessPolicyReceipt,
    build_coverage_gap_snapshot,
    build_subprocess_policy_receipt,
    receipt_digest,
    write_receipt,
)


def _passing_command(label: str) -> CommandReceipt:
    return CommandReceipt(("python", "-c", label), "pass", 0, 0.1)


def test_release_metadata_never_inferrs_authority() -> None:
    receipt = ReleaseMetadataReceipt("owner/repo", "abc123", "v1", "pass")
    assert any("branch protection" in error for error in receipt.validate())
    assert any("private promotion" in error for error in receipt.validate())


def test_clean_checkout_requires_two_runs_and_clean_outputs() -> None:
    receipt = CleanCheckoutReceipt("abc123", "darwin-arm64", "pass", (_passing_command("one"),))
    assert any("two deterministic runs" in error for error in receipt.validate())

    complete = CleanCheckoutReceipt(
        "abc123",
        "darwin-arm64",
        "pass",
        (_passing_command("one"), _passing_command("two")),
        output_clean=True,
    )
    assert complete.validate() == []


def test_skipped_receipt_requires_reason() -> None:
    receipt = CommandReceipt(("tool",), "skipped", None, 0.0)
    assert any("skip_reason" in error for error in receipt.validate())


def test_coverage_snapshot_fails_closed_on_missing_measurement() -> None:
    receipt = CoverageGapSnapshot(
        revision="abc123",
        infrastructure_percent=80.0,
        infrastructure_floor=60.0,
        projects={"templates/demo": None},
        project_floors={"templates/demo": 90.0},
        status="pass",
    )
    assert any("templates/demo" in error for error in receipt.validate())


def test_policy_receipt_is_sorted_and_digestable(tmp_path: Path) -> None:
    rows = (
        SubprocessPolicyRecord("b", "b.py", 2, True, False, True, True, True),
        SubprocessPolicyRecord("a", "a.py", 1, True, False, True, True, True),
    )
    receipt = SubprocessPolicyReceipt(rows)
    assert receipt.validate() == []
    assert [row["policy_id"] for row in receipt.to_dict()["policies"]] == ["a", "b"]
    assert len(receipt_digest(receipt)) == 64
    path = write_receipt(tmp_path / "receipt.json", receipt)
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_command_receipt_rejects_secret_like_arguments() -> None:
    receipt = CommandReceipt(("tool", "--api-key", "value"), "pass", 0, 0.0)
    assert any("credential-like" in error for error in receipt.validate())


def test_blocked_command_receipt_preserves_actionable_failure_reason() -> None:
    receipt = CommandReceipt(("tool",), "blocked", 2, 0.2, skip_reason="tool failed")
    assert receipt.validate() == []


def test_subprocess_policy_builder_binds_to_source_inventory() -> None:
    root = Path(__file__).resolve().parents[3]
    receipt = build_subprocess_policy_receipt(root)
    assert receipt.status == "pass"
    assert len(receipt.policies) >= 10
    assert receipt.validate() == []


def test_coverage_snapshot_builder_keeps_missing_measurements_reviewable() -> None:
    snapshot = build_coverage_gap_snapshot(
        revision="abc123",
        infrastructure_percent=None,
        infrastructure_floor=60.0,
        projects={"templates/demo": None},
        project_floors={"templates/demo": 90.0},
    )
    assert snapshot.status == "review_required"
    assert snapshot.infrastructure_percent is None
    assert snapshot.skip_reason
