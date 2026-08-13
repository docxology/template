"""Behavioral tests for versioned, authority-aware release receipts."""

from __future__ import annotations

import hashlib
from pathlib import Path

from infrastructure.core.subprocess_policy import SubprocessPolicyRecord
from infrastructure.publishing.release_receipts import (
    CleanCheckoutReceipt,
    CommandReceipt,
    CoverageGapSnapshot,
    ReleaseMetadataReceipt,
    SubprocessPolicyReceipt,
    build_coverage_gap_snapshot,
    build_release_metadata_receipt,
    build_subprocess_policy_receipt,
    receipt_digest,
    write_receipt,
)


def _passing_command(label: str) -> CommandReceipt:
    return CommandReceipt(
        ("python", "-c", label),
        "pass",
        0,
        0.1,
        output_sha256=hashlib.sha256(label.encode("utf-8")).hexdigest(),
    )


def test_release_metadata_never_inferrs_authority() -> None:
    receipt = ReleaseMetadataReceipt("owner/repo", "abc123", "v1", "pass")
    assert any("branch protection" in error for error in receipt.validate())
    assert any("private promotion" in error for error in receipt.validate())


def test_release_metadata_binds_status_to_command_scope_and_date() -> None:
    receipt = build_release_metadata_receipt(
        repository="owner/repo",
        revision="abc123",
        version="v1",
        command=("uv", "run", "python", "scripts/check.py"),
        scope=("root package", "public roster"),
        owner="maintainer",
        checked_at="2026-08-10",
        health="review required",
        source_urls=("https://github.com/owner/repo",),
    )
    assert receipt.validate() == []
    payload = receipt.to_dict()
    assert payload["scope"] == ["root package", "public roster"]
    assert payload["command"][-1] == "scripts/check.py"


def test_release_metadata_rejects_credential_url_and_missing_scope() -> None:
    receipt = ReleaseMetadataReceipt(
        "owner/repo",
        "abc123",
        "v1",
        "review_required",
        scope=(),
        command=("tool",),
        owner="maintainer",
        checked_at="2026-08-10",
        health="review required",
        source_urls=("https://example.invalid/?api_key=secret",),
    )
    errors = receipt.validate()
    assert any("non-empty scope" in error for error in errors)
    assert any("credential-free HTTPS" in error for error in errors)


def test_clean_checkout_requires_two_runs_and_clean_outputs() -> None:
    receipt = CleanCheckoutReceipt("abc123", "darwin-arm64", "pass", (_passing_command("one"),))
    assert any("two deterministic runs" in error for error in receipt.validate())

    complete = CleanCheckoutReceipt(
        "abc123",
        "darwin-arm64",
        "pass",
        (_passing_command("same"), _passing_command("same")),
        run_commands=(
            (_passing_command("same"),),
            (_passing_command("same"),),
        ),
        output_clean=True,
    )
    assert complete.validate() == []

    nondeterministic = CleanCheckoutReceipt(
        "abc123",
        "darwin-arm64",
        "pass",
        (_passing_command("one"), _passing_command("two")),
        output_clean=True,
    )
    assert any("different deterministic output digests" in error for error in nondeterministic.validate())

    third_run_failure = CleanCheckoutReceipt(
        "abc123",
        "darwin-arm64",
        "pass",
        (
            _passing_command("same"),
            _passing_command("same"),
            CommandReceipt(
                ("pytest",),
                "blocked",
                2,
                0.1,
                skip_reason="tool unavailable",
                output_sha256=_passing_command("same").output_sha256,
            ),
        ),
        run_commands=(
            (_passing_command("same"),),
            (_passing_command("same"),),
            (CommandReceipt(("pytest",), "blocked", 2, 0.1, skip_reason="tool unavailable"),),
        ),
        output_clean=True,
    )
    assert any("all clean-checkout runs must pass" in error for error in third_run_failure.validate())


def test_command_receipt_rejects_non_hex_sha256() -> None:
    receipt = CommandReceipt(("tool",), "pass", 0, 0.0, output_sha256="z" * 64)
    assert any("lowercase SHA-256" in error for error in receipt.validate())


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
