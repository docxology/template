"""Real-behavior tests for the additional organization-specific release policies."""

from __future__ import annotations

import pytest

from redacted_report import (
    RedactionDecision,
    RedactionPolicy,
    RedactionSegment,
    ReviewRecord,
    audit_release_packet,
    declared_release_policies,
    detect_residual_risks,
    evaluate_review_gate,
)


def _minimal_segments(policy: RedactionPolicy, *, sensitive: bool = True) -> list[RedactionSegment]:
    labels = list(policy.taxonomy.order)
    if sensitive:
        return [
            RedactionSegment("s1", labels[0], "Public opening sentence.", ()),
            RedactionSegment("s2", labels[-1], "Sensitive detail with selector at 38.8977, -77.0365.", ("HUMINT",)),
        ]
    return [
        RedactionSegment("s1", labels[0], "Public opening sentence.", ()),
        RedactionSegment("s2", labels[0], "Second public sentence.", ()),
    ]


def _approving_reviews(policy: RedactionPolicy) -> list[ReviewRecord]:
    return [
        ReviewRecord(f"{role}-a", role, "approve", f"invented fixture cleared by {role}")
        for role in policy.required_review_roles
    ]


def test_declared_policies_are_distinct_and_configured() -> None:
    policies = declared_release_policies()

    assert len(policies) == 4
    assert len({policy.name for policy in policies}) == 4
    for policy in policies:
        order = list(policy.taxonomy.order.values())
        assert order == sorted(order), f"{policy.name}: taxonomy order must be strictly increasing"
        assert len(order) >= 2
        assert policy.public_ceiling == list(policy.taxonomy.order)[0]
        assert policy.required_review_roles
        assert policy.minimum_approvals >= 1
        assert policy.minimum_approvals <= len(policy.required_review_roles)
        assert 0.0 < policy.mosaic_threshold <= 1.0
        assert policy.taxonomy.name
        assert any(entry.name == "email_address" for entry in policy.residual_patterns)


def test_intelligence_policy_is_the_unchanged_regression_surface() -> None:
    policies = {policy.name: policy for policy in declared_release_policies()}
    intelligence = policies["intelligence_release_review"]

    assert intelligence.public_ceiling == "UNCLASSIFIED"
    assert intelligence.required_review_roles == ("originator", "classification_reviewer", "release_authority")
    assert intelligence.minimum_approvals == 3
    assert intelligence.mosaic_threshold == 0.30
    assert intelligence.block_warnings is True


@pytest.mark.parametrize("policy_name", [policy.name for policy in declared_release_policies()])
def test_each_policy_audits_and_approves_its_own_minimal_fixture(policy_name: str) -> None:
    policies = {policy.name: policy for policy in declared_release_policies()}
    policy = policies[policy_name]
    segments = _minimal_segments(policy)
    decisions = [
        RedactionDecision("s2", 0, 15, "source_identity"),
        RedactionDecision("s2", 28, 49, "time_place_selector"),
    ]

    audit = audit_release_packet(
        segments,
        decisions,
        release_authority="public-affairs-review-board",
        public_ceiling=policy.public_ceiling,
        mosaic_threshold=policy.mosaic_threshold,
        taxonomy=policy.taxonomy,
        policy=policy,
    )
    gate = evaluate_review_gate(_approving_reviews(policy), policy)

    assert audit.releasable is True, f"{policy.name}: {[f.message for f in audit.findings]}"
    assert audit.redaction_coverage == 1.0
    assert gate.approved is True, f"{policy.name}: {[f.message for f in gate.findings]}"
    assert gate.approval_count == len(policy.required_review_roles)


@pytest.mark.parametrize("policy_name", [policy.name for policy in declared_release_policies()])
def test_each_policy_rejects_when_a_required_role_is_missing(policy_name: str) -> None:
    policies = {policy.name: policy for policy in declared_release_policies()}
    policy = policies[policy_name]
    reviews = _approving_reviews(policy)[:-1]

    gate = evaluate_review_gate(reviews, policy)

    assert gate.approved is False
    assert any(finding.code == "missing_required_role" for finding in gate.findings)


@pytest.mark.parametrize("policy_name", [policy.name for policy in declared_release_policies()])
def test_each_policy_blocks_unknown_classifications(policy_name: str) -> None:
    policies = {policy.name: policy for policy in declared_release_policies()}
    policy = policies[policy_name]
    segments = [RedactionSegment("s1", "NOT_A_CLASSIFICATION", "text", ())]

    audit = audit_release_packet(
        segments,
        [],
        release_authority="public-affairs-review-board",
        public_ceiling=policy.public_ceiling,
        taxonomy=policy.taxonomy,
        policy=policy,
    )

    assert audit.releasable is False
    assert any(finding.code == "unknown_classification" for finding in audit.findings)


def test_policy_specific_residual_patterns_fire_on_invented_markers() -> None:
    policies = {policy.name: policy for policy in declared_release_policies()}
    expectations = {
        "intelligence_release_review": ("NOFORN", "controlled_dissemination"),
        "law_enforcement_release_review": ("CASE_NUMBER-4471", "person_identifying_data"),
        "public_records_release_review": ("PHONE 555-0100", "personal_identifier"),
        "health_privacy_release_review": ("HIPAA notice", "phi_marker"),
    }
    for policy_name, (marker, expected_name) in expectations.items():
        policy = policies[policy_name]
        risks = detect_residual_risks(f"unredacted {marker} remains", policy)
        assert any(risk["name"] == expected_name for risk in risks), f"{policy_name}: {marker}"


def test_health_privacy_policy_treats_phi_above_ceiling() -> None:
    policy = {p.name: p for p in declared_release_policies()}["health_privacy_release_review"]
    segments = [
        RedactionSegment("s1", "PUBLIC", "Public statement.", ()),
        RedactionSegment("s2", "PHI", "PHI detail with no redaction.", ()),
    ]

    audit = audit_release_packet(
        segments,
        [],
        release_authority="public-affairs-review-board",
        public_ceiling=policy.public_ceiling,
        taxonomy=policy.taxonomy,
        policy=policy,
    )

    assert audit.releasable is False
    assert any(finding.code == "above_ceiling_unredacted" for finding in audit.findings)
