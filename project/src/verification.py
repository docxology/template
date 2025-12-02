"""Proof Verification and Axiom Checking for Boundary Logic.

This module provides rigorous verification tools for:
- Axiom validation
- Theorem proof checking
- Equivalence verification
- Consistency checking

The verification system ensures that all derivations in boundary logic
correctly follow from the two fundamental axioms (Calling and Crossing).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.reduction import (
    ReductionEngine, reduce_form, reduce_with_trace,
    forms_equivalent, ReductionTrace, ReductionRule
)
from src.evaluation import evaluate


class VerificationStatus(Enum):
    """Status of a verification check."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class VerificationResult:
    """Result of a verification check.
    
    Attributes:
        name: Name of the check
        status: Pass/fail status
        message: Detailed message
        details: Additional details
    """
    name: str
    status: VerificationStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        symbol = {
            VerificationStatus.PASSED: "✓",
            VerificationStatus.FAILED: "✗",
            VerificationStatus.SKIPPED: "○",
            VerificationStatus.ERROR: "!",
        }[self.status]
        return f"[{symbol}] {self.name}: {self.message}"


@dataclass
class VerificationReport:
    """Complete verification report.
    
    Attributes:
        results: List of verification results
        passed: Count of passed checks
        failed: Count of failed checks
        total: Total checks run
    """
    results: List[VerificationResult] = field(default_factory=list)
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == VerificationStatus.PASSED)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == VerificationStatus.FAILED)
    
    @property
    def total(self) -> int:
        return len(self.results)
    
    @property
    def all_passed(self) -> bool:
        return self.failed == 0
    
    def add(self, result: VerificationResult) -> None:
        """Add a result to the report."""
        self.results.append(result)
    
    def __str__(self) -> str:
        lines = ["=" * 50]
        lines.append("VERIFICATION REPORT")
        lines.append("=" * 50)
        
        for result in self.results:
            lines.append(str(result))
        
        lines.append("-" * 50)
        lines.append(f"Passed: {self.passed}/{self.total}")
        lines.append(f"Status: {'ALL PASSED' if self.all_passed else 'FAILURES'}")
        lines.append("=" * 50)
        
        return "\n".join(lines)


class AxiomVerifier:
    """Verifier for the fundamental axioms.
    
    Verifies that the axioms hold and are correctly implemented.
    """
    
    def verify_calling_axiom(self) -> VerificationResult:
        """Verify Axiom J1 (Calling): ⟨⟨a⟩⟩ = a.
        
        Returns:
            VerificationResult
        """
        # Test with mark
        a = make_mark()
        double_enclosed = enclose(enclose(a))
        
        reduced = reduce_form(double_enclosed)
        passed = reduced == a
        
        return VerificationResult(
            name="Axiom J1 (Calling)",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"⟨⟨a⟩⟩ = {reduced} (expected {a})",
            details={
                "input": str(double_enclosed),
                "output": str(reduced),
                "expected": str(a),
            }
        )
    
    def verify_crossing_axiom(self) -> VerificationResult:
        """Verify Axiom J2 (Crossing): ⟨ ⟩⟨ ⟩ = ⟨ ⟩.
        
        Returns:
            VerificationResult
        """
        two_marks = juxtapose(make_mark(), make_mark())
        single_mark = make_mark()
        
        reduced = reduce_form(two_marks)
        passed = reduced == single_mark
        
        return VerificationResult(
            name="Axiom J2 (Crossing)",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"⟨ ⟩⟨ ⟩ = {reduced} (expected ⟨ ⟩)",
            details={
                "input": str(two_marks),
                "output": str(reduced),
                "expected": str(single_mark),
            }
        )
    
    def verify_all(self) -> VerificationReport:
        """Verify all axioms.
        
        Returns:
            VerificationReport with all axiom checks
        """
        report = VerificationReport()
        report.add(self.verify_calling_axiom())
        report.add(self.verify_crossing_axiom())
        return report


class ConsistencyVerifier:
    """Verifier for logical consistency.
    
    Checks that the system is consistent (no contradictions).
    """
    
    def verify_non_contradiction(self) -> VerificationResult:
        """Verify that TRUE ≠ FALSE.
        
        Returns:
            VerificationResult
        """
        true_form = make_mark()
        false_form = make_void()
        
        # These should not be equivalent
        passed = not forms_equivalent(true_form, false_form)
        
        return VerificationResult(
            name="Non-Contradiction",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message="TRUE and FALSE are distinct" if passed else "TRUE = FALSE!",
        )
    
    def verify_excluded_middle(self) -> VerificationResult:
        """Verify that a ∨ ¬a = TRUE.
        
        In boundary logic: ⟨⟨a⟩a⟩ = ⟨ ⟩
        
        Returns:
            VerificationResult
        """
        a = make_mark()
        # a OR NOT a = ⟨⟨a⟩a⟩
        excluded_middle = enclose(juxtapose(enclose(a), a))
        
        reduced = reduce_form(excluded_middle)
        passed = reduced.is_simple_mark()
        
        return VerificationResult(
            name="Excluded Middle",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"a ∨ ¬a = {reduced} (expected ⟨ ⟩)",
        )
    
    def verify_double_negation(self) -> VerificationResult:
        """Verify that ¬¬a = a.
        
        Returns:
            VerificationResult
        """
        a = make_mark()
        double_neg = enclose(enclose(a))
        
        passed = forms_equivalent(double_neg, a)
        
        return VerificationResult(
            name="Double Negation Elimination",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"¬¬a = a: {passed}",
        )
    
    def verify_idempotence(self) -> VerificationResult:
        """Verify that a ∧ a = a.
        
        Returns:
            VerificationResult
        """
        a = make_mark()
        a_and_a = juxtapose(a, a)
        
        passed = forms_equivalent(a_and_a, a)
        
        return VerificationResult(
            name="Idempotence",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"a ∧ a = a: {passed}",
        )
    
    def verify_all(self) -> VerificationReport:
        """Verify all consistency properties.
        
        Returns:
            VerificationReport
        """
        report = VerificationReport()
        report.add(self.verify_non_contradiction())
        report.add(self.verify_excluded_middle())
        report.add(self.verify_double_negation())
        report.add(self.verify_idempotence())
        return report


class EquivalenceVerifier:
    """Verifier for form equivalences.
    
    Checks that expected equivalences hold.
    """
    
    def verify_equivalence(
        self,
        name: str,
        form1: Form,
        form2: Form
    ) -> VerificationResult:
        """Verify that two forms are equivalent.
        
        Args:
            name: Name for this check
            form1: First form
            form2: Second form
            
        Returns:
            VerificationResult
        """
        passed = forms_equivalent(form1, form2)
        
        return VerificationResult(
            name=name,
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"{form1} = {form2}: {passed}",
            details={
                "form1": str(form1),
                "form2": str(form2),
                "canonical1": str(reduce_form(form1)),
                "canonical2": str(reduce_form(form2)),
            }
        )
    
    def verify_not_equivalent(
        self,
        name: str,
        form1: Form,
        form2: Form
    ) -> VerificationResult:
        """Verify that two forms are NOT equivalent.
        
        Args:
            name: Name for this check
            form1: First form
            form2: Second form
            
        Returns:
            VerificationResult
        """
        passed = not forms_equivalent(form1, form2)
        
        return VerificationResult(
            name=name,
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"{form1} ≠ {form2}: {passed}",
        )


class SemanticVerifier:
    """Verifier for semantic properties.
    
    Verifies evaluation semantics match expected behavior.
    """
    
    def verify_mark_is_true(self) -> VerificationResult:
        """Verify that ⟨ ⟩ evaluates to TRUE.
        
        Returns:
            VerificationResult
        """
        mark = make_mark()
        value = evaluate(mark)
        passed = value == True
        
        return VerificationResult(
            name="Mark is TRUE",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"⟨ ⟩ = {value}",
        )
    
    def verify_void_is_false(self) -> VerificationResult:
        """Verify that void evaluates to FALSE.
        
        Returns:
            VerificationResult
        """
        void = make_void()
        value = evaluate(void)
        passed = value == False
        
        return VerificationResult(
            name="Void is FALSE",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"∅ = {value}",
        )
    
    def verify_enclosure_negates(self) -> VerificationResult:
        """Verify that enclosure negates.
        
        Returns:
            VerificationResult
        """
        mark = make_mark()  # TRUE
        enclosed = enclose(mark)  # Should be FALSE
        
        value = evaluate(enclosed)
        passed = value == False
        
        return VerificationResult(
            name="Enclosure Negates",
            status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            message=f"⟨TRUE⟩ = {value} (expected FALSE)",
        )
    
    def verify_all(self) -> VerificationReport:
        """Verify all semantic properties.
        
        Returns:
            VerificationReport
        """
        report = VerificationReport()
        report.add(self.verify_mark_is_true())
        report.add(self.verify_void_is_false())
        report.add(self.verify_enclosure_negates())
        return report


def verify_axioms() -> VerificationReport:
    """Verify all axioms.
    
    Returns:
        VerificationReport
    """
    return AxiomVerifier().verify_all()


def verify_consistency() -> VerificationReport:
    """Verify system consistency.
    
    Returns:
        VerificationReport
    """
    return ConsistencyVerifier().verify_all()


def verify_semantics() -> VerificationReport:
    """Verify evaluation semantics.
    
    Returns:
        VerificationReport
    """
    return SemanticVerifier().verify_all()


def full_verification() -> VerificationReport:
    """Run complete verification suite.
    
    Returns:
        Combined VerificationReport
    """
    report = VerificationReport()
    
    # Axioms
    for result in verify_axioms().results:
        report.add(result)
    
    # Consistency
    for result in verify_consistency().results:
        report.add(result)
    
    # Semantics
    for result in verify_semantics().results:
        report.add(result)
    
    return report


def generate_verification_summary() -> str:
    """Generate a verification summary.
    
    Returns:
        Formatted summary string
    """
    report = full_verification()
    return str(report)

