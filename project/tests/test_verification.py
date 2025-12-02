"""Tests for proof verification and axiom checking.

Tests cover:
- Axiom verification
- Consistency checks
- Semantic verification
- Full verification suite
"""
import pytest
from src.forms import make_void, make_mark, enclose, juxtapose
from src.verification import (
    VerificationStatus, VerificationResult, VerificationReport,
    AxiomVerifier, ConsistencyVerifier, SemanticVerifier,
    verify_axioms, verify_consistency, verify_semantics,
    full_verification, generate_verification_summary
)


class TestVerificationResult:
    """Tests for VerificationResult class."""
    
    def test_passed_result(self):
        """Test passed result creation."""
        result = VerificationResult(
            name="Test",
            status=VerificationStatus.PASSED,
            message="All good"
        )
        assert result.status == VerificationStatus.PASSED
    
    def test_failed_result(self):
        """Test failed result creation."""
        result = VerificationResult(
            name="Test",
            status=VerificationStatus.FAILED,
            message="Problem found"
        )
        assert result.status == VerificationStatus.FAILED
    
    def test_result_string(self):
        """Test result string representation."""
        result = VerificationResult(
            name="Test",
            status=VerificationStatus.PASSED,
            message="OK"
        )
        assert "✓" in str(result) or "Test" in str(result)


class TestVerificationReport:
    """Tests for VerificationReport class."""
    
    def test_empty_report(self):
        """Test empty report."""
        report = VerificationReport()
        assert report.total == 0
        assert report.passed == 0
        assert report.failed == 0
    
    def test_add_result(self):
        """Test adding result to report."""
        report = VerificationReport()
        report.add(VerificationResult("Test", VerificationStatus.PASSED))
        assert report.total == 1
        assert report.passed == 1
    
    def test_all_passed(self):
        """Test all_passed property."""
        report = VerificationReport()
        report.add(VerificationResult("Test1", VerificationStatus.PASSED))
        report.add(VerificationResult("Test2", VerificationStatus.PASSED))
        assert report.all_passed
    
    def test_has_failure(self):
        """Test report with failure."""
        report = VerificationReport()
        report.add(VerificationResult("Test1", VerificationStatus.PASSED))
        report.add(VerificationResult("Test2", VerificationStatus.FAILED))
        assert not report.all_passed
        assert report.failed == 1


class TestAxiomVerifier:
    """Tests for axiom verification."""
    
    def test_calling_axiom_verified(self):
        """Test J1 (Calling) axiom is verified."""
        verifier = AxiomVerifier()
        result = verifier.verify_calling_axiom()
        assert result.status == VerificationStatus.PASSED
    
    def test_crossing_axiom_verified(self):
        """Test J2 (Crossing) axiom is verified."""
        verifier = AxiomVerifier()
        result = verifier.verify_crossing_axiom()
        assert result.status == VerificationStatus.PASSED
    
    def test_verify_all_axioms(self):
        """Test all axioms verified."""
        verifier = AxiomVerifier()
        report = verifier.verify_all()
        assert report.all_passed
        assert report.total == 2


class TestConsistencyVerifier:
    """Tests for consistency verification."""
    
    def test_non_contradiction(self):
        """Test non-contradiction verified."""
        verifier = ConsistencyVerifier()
        result = verifier.verify_non_contradiction()
        assert result.status == VerificationStatus.PASSED
    
    def test_excluded_middle(self):
        """Test excluded middle verified."""
        verifier = ConsistencyVerifier()
        result = verifier.verify_excluded_middle()
        assert result.status == VerificationStatus.PASSED
    
    def test_double_negation(self):
        """Test double negation verified."""
        verifier = ConsistencyVerifier()
        result = verifier.verify_double_negation()
        assert result.status == VerificationStatus.PASSED
    
    def test_idempotence(self):
        """Test idempotence verified."""
        verifier = ConsistencyVerifier()
        result = verifier.verify_idempotence()
        assert result.status == VerificationStatus.PASSED
    
    def test_verify_all_consistency(self):
        """Test all consistency checks pass."""
        verifier = ConsistencyVerifier()
        report = verifier.verify_all()
        assert report.all_passed


class TestSemanticVerifier:
    """Tests for semantic verification."""
    
    def test_mark_is_true(self):
        """Test mark is TRUE verified."""
        verifier = SemanticVerifier()
        result = verifier.verify_mark_is_true()
        assert result.status == VerificationStatus.PASSED
    
    def test_void_is_false(self):
        """Test void is FALSE verified."""
        verifier = SemanticVerifier()
        result = verifier.verify_void_is_false()
        assert result.status == VerificationStatus.PASSED
    
    def test_enclosure_negates(self):
        """Test enclosure negates verified."""
        verifier = SemanticVerifier()
        result = verifier.verify_enclosure_negates()
        assert result.status == VerificationStatus.PASSED
    
    def test_verify_all_semantics(self):
        """Test all semantic checks pass."""
        verifier = SemanticVerifier()
        report = verifier.verify_all()
        assert report.all_passed


class TestVerificationFunctions:
    """Tests for verification convenience functions."""
    
    def test_verify_axioms(self):
        """Test verify_axioms function."""
        report = verify_axioms()
        assert report.all_passed
    
    def test_verify_consistency(self):
        """Test verify_consistency function."""
        report = verify_consistency()
        assert report.all_passed
    
    def test_verify_semantics(self):
        """Test verify_semantics function."""
        report = verify_semantics()
        assert report.all_passed
    
    def test_full_verification(self):
        """Test full_verification function."""
        report = full_verification()
        assert report.all_passed
        assert report.total >= 9  # At least 2 axioms + 4 consistency + 3 semantic
    
    def test_generate_summary(self):
        """Test summary generation."""
        summary = generate_verification_summary()
        assert "VERIFICATION REPORT" in summary
        assert "PASSED" in summary or "passed" in summary.lower()

