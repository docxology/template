"""Negative controls for the opt-in SIA fork approval boundary."""

from __future__ import annotations

from src.approval import APPROVAL_SCHEMA, ApprovalContract, validate_approval_contract


def test_fixture_replay_does_not_require_or_claim_approval() -> None:
    contract = ApprovalContract(mode="fixture_replay")
    assert contract.validate() == ()
    assert contract.to_dict()["schema_version"] == APPROVAL_SCHEMA


def test_live_apply_requires_sandbox_diff_rollback_and_owner_receipt() -> None:
    contract = ApprovalContract(mode="live_apply", approval_status="pending")
    issues = contract.validate()

    assert any("sandbox_root" in issue for issue in issues)
    assert any("diff digest" in issue for issue in issues)
    assert any("rollback digest" in issue for issue in issues)
    assert any("approved" in issue for issue in issues)
    assert any("approval_receipt_id" in issue for issue in issues)


def test_live_proposal_with_digests_can_remain_pending() -> None:
    digest = "a" * 64
    contract = ApprovalContract(
        mode="live_proposal",
        sandbox_root="sandbox/run-1",
        diff_sha256=digest,
        rollback_sha256=digest,
        approval_status="pending",
    )
    assert contract.validate() == ()


def test_malformed_approval_payload_fails_closed() -> None:
    issues = validate_approval_contract(
        {
            "schema_version": APPROVAL_SCHEMA,
            "mode": "live_apply",
            "sandbox_root": "sandbox",
            "diff_sha256": "not-a-digest",
            "rollback_sha256": "not-a-digest",
            "approval_status": "pending",
        }
    )
    assert any("SHA-256" in issue for issue in issues)
    assert any("approved" in issue for issue in issues)
