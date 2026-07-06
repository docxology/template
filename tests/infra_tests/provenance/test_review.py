"""Tests for infrastructure.provenance.review."""

from __future__ import annotations

import pytest

from infrastructure.provenance import (
    ArtifactNode,
    ClaimNode,
    Finding,
    NodeKind,
    Provenance,
    Review,
    ReviewResult,
    RunNode,
    Severity,
    SourceNode,
    review_provenance_store,
)


class TestSeverity:
    def test_ordering_exists(self):
        assert Severity.critical != Severity.info
        assert {s.value for s in Severity} == {"info", "warning", "error", "critical"}


class TestFinding:
    def test_to_dict(self):
        f = Finding(
            node_id="abc",
            severity=Severity.warning,
            code="missing_hash",
            message="No hash found.",
        )
        d = f.to_dict()
        assert d["severity"] == "warning"
        assert d["code"] == "missing_hash"
        assert d["node_id"] == "abc"

    def test_frozen(self):
        f = Finding(node_id="x", severity=Severity.info, code="c", message="m")
        with pytest.raises((AttributeError, TypeError)):
            f.code = "new"  # type: ignore[misc]


class TestReviewResult:
    def test_passed_no_errors(self):
        r = ReviewResult(findings=[
            Finding(node_id="a", severity=Severity.info, code="c", message="m"),
            Finding(node_id="b", severity=Severity.warning, code="c", message="m"),
        ])
        assert r.passed is True

    def test_failed_on_error(self):
        r = ReviewResult(findings=[
            Finding(node_id="a", severity=Severity.error, code="c", message="m"),
        ])
        assert r.passed is False

    def test_failed_on_critical(self):
        r = ReviewResult(findings=[
            Finding(node_id="a", severity=Severity.critical, code="c", message="m"),
        ])
        assert r.passed is False

    def test_by_severity(self):
        r = ReviewResult(findings=[
            Finding(node_id="a", severity=Severity.info, code="c", message="m"),
            Finding(node_id="b", severity=Severity.warning, code="w", message="m"),
            Finding(node_id="c", severity=Severity.info, code="i2", message="m"),
        ])
        info = r.by_severity(Severity.info)
        assert len(info) == 2

    def test_to_dict(self):
        r = ReviewResult()
        d = r.to_dict()
        assert d["passed"] is True
        assert d["findings"] == []


class TestReview:
    def test_record_and_result(self):
        rev = Review()
        rev.record(Finding(node_id="x", severity=Severity.info, code="c", message="m"))
        result = rev.result()
        assert len(result.findings) == 1

    def test_findings_for_node(self):
        rev = Review()
        rev.record(Finding(node_id="n1", severity=Severity.info, code="c1", message="m"))
        rev.record(Finding(node_id="n2", severity=Severity.warning, code="c2", message="m"))
        rev.record(Finding(node_id="n1", severity=Severity.error, code="c3", message="m"))
        findings = rev.findings_for_node("n1")
        assert len(findings) == 2
        assert all(f.node_id == "n1" for f in findings)

    def test_clear(self):
        rev = Review()
        rev.record(Finding(node_id="x", severity=Severity.info, code="c", message="m"))
        rev.clear()
        assert len(rev) == 0

    def test_repr(self):
        rev = Review()
        assert "Review" in repr(rev)

    def test_len(self):
        rev = Review()
        assert len(rev) == 0
        rev.record(Finding(node_id="x", severity=Severity.info, code="c", message="m"))
        assert len(rev) == 1


class TestReviewProvenanceStore:
    def test_missing_hash_warning(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = ArtifactNode.create("fig", path="fig.pdf")
        # no content_hash
        prov.record(n)
        result = review_provenance_store(prov)
        codes = [f.code for f in result.findings]
        assert "missing_hash" in codes

    def test_artifact_with_hash_passes(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = ArtifactNode.create("fig", path="fig.pdf", content_hash="abc123")
        prov.record(n)
        result = review_provenance_store(prov)
        codes = [f.code for f in result.findings]
        assert "missing_hash" not in codes

    def test_source_missing_uri_error(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = SourceNode.create("src", uri="")  # empty URI
        prov.record(n)
        result = review_provenance_store(prov)
        codes = [f.code for f in result.findings]
        assert "missing_uri" in codes

    def test_claim_zero_confidence_warning(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = ClaimNode.create("c", "text", confidence=0.0)
        prov.record(n)
        result = review_provenance_store(prov)
        codes = [f.code for f in result.findings]
        assert "zero_confidence" in codes

    def test_run_missing_exit_code_info(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = RunNode.create("r", command="cmd")  # exit_code=None
        prov.record(n)
        result = review_provenance_store(prov)
        codes = [f.code for f in result.findings]
        assert "missing_exit_code" in codes

    def test_run_with_exit_code_passes(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        n = RunNode.create("r", command="cmd", exit_code=0)
        prov.record(n)
        result = review_provenance_store(prov)
        codes = [f.code for f in result.findings]
        assert "missing_exit_code" not in codes

    def test_empty_store_passes(self, tmp_path):
        prov = Provenance.with_path(tmp_path)
        result = review_provenance_store(prov)
        assert result.passed is True
        assert result.findings == []
