"""Tests for src.assay — claim evidence validation."""

from __future__ import annotations

import pytest

from assay import (
    AssayReport,
    ClaimRecord,
    assay_claims,
    compute_assay_purity,
)


class TestClaimRecord:
    def test_valid_record(self):
        claim = ClaimRecord(
            claim_id="C1",
            statement="The sky is blue",
            evidence_type="citation",
            evidence_ref="smith2024",
            supported=True,
        )
        assert claim.claim_id == "C1"
        assert claim.supported is True

    def test_empty_claim_id_raises(self):
        with pytest.raises(ValueError, match="claim_id must not be empty"):
            ClaimRecord(
                claim_id="",
                statement="test",
                evidence_type="none",
                evidence_ref="",
                supported=False,
            )

    def test_invalid_evidence_type_raises(self):
        with pytest.raises(ValueError, match="evidence_type"):
            ClaimRecord(
                claim_id="C1",
                statement="test",
                evidence_type="invalid",
                evidence_ref="",
                supported=False,
            )

    def test_all_evidence_types(self):
        for etype in ("citation", "figure", "table", "computation", "none"):
            claim = ClaimRecord(
                claim_id=f"C_{etype}",
                statement="test",
                evidence_type=etype,
                evidence_ref="ref",
                supported=True,
            )
            assert claim.evidence_type == etype


class TestAssayReport:
    def test_empty_report(self):
        report = AssayReport()
        assert report.total_claims == 0
        assert report.supported_claims == 0
        assert report.unsupported_claims == 0
        assert report.support_rate == 0.0
        assert report.assay_purity == 0.0
        assert report.is_passing is False

    def test_all_supported(self):
        claims = [
            ClaimRecord("C1", "stmt", "citation", "ref", True),
            ClaimRecord("C2", "stmt", "figure", "fig1", True),
        ]
        report = assay_claims(claims)
        assert report.total_claims == 2
        assert report.supported_claims == 2
        assert report.unsupported_claims == 0
        assert report.support_rate == 1.0
        assert report.assay_purity == 1.0
        assert report.is_passing is True

    def test_partial_support(self):
        claims = [
            ClaimRecord("C1", "stmt", "citation", "ref", True),
            ClaimRecord("C2", "stmt", "none", "", False),
        ]
        report = assay_claims(claims)
        assert report.total_claims == 2
        assert report.supported_claims == 1
        assert report.unsupported_claims == 1
        assert report.support_rate == 0.5
        assert report.assay_purity == 0.5
        assert report.is_passing is False

    def test_none_supported(self):
        claims = [
            ClaimRecord("C1", "stmt", "none", "", False),
            ClaimRecord("C2", "stmt", "none", "", False),
        ]
        report = assay_claims(claims)
        assert report.support_rate == 0.0
        assert report.assay_purity == 0.0
        assert report.is_passing is False


class TestComputeAssayPurity:
    def test_empty_claims(self):
        assert compute_assay_purity([]) == 0.0

    def test_all_supported(self):
        claims = [
            ClaimRecord("C1", "stmt", "citation", "ref", True),
            ClaimRecord("C2", "stmt", "citation", "ref", True),
        ]
        assert compute_assay_purity(claims) == 1.0

    def test_half_supported(self):
        claims = [
            ClaimRecord("C1", "stmt", "citation", "ref", True),
            ClaimRecord("C2", "stmt", "none", "", False),
        ]
        assert compute_assay_purity(claims) == 0.5
