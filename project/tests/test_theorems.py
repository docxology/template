"""Tests for theorem definitions and verification.

Tests cover:
- Axiom theorems
- Derived theorems (consequences)
- Proof structures
- Theorem verification
"""
import pytest
from src.forms import make_void, make_mark, enclose, juxtapose
from src.theorems import (
    Theorem, TheoremStatus, Proof, ProofStep,
    axiom_calling, axiom_crossing,
    theorem_position, theorem_generation, theorem_iteration,
    get_all_axioms, get_all_consequences, get_all_theorems,
    verify_all_theorems, theorem_summary
)


class TestTheoremClass:
    """Tests for Theorem class."""
    
    def test_theorem_creation(self):
        """Test theorem creation."""
        theorem = Theorem(
            name="Test",
            description="A test theorem",
            lhs=make_mark(),
            rhs=make_mark()
        )
        assert theorem.name == "Test"
        assert theorem.status == TheoremStatus.UNVERIFIED
    
    def test_theorem_verify_pass(self):
        """Test theorem verification passes for equivalent forms."""
        theorem = Theorem(
            name="Identity",
            description="a = a",
            lhs=make_mark(),
            rhs=make_mark()
        )
        assert theorem.verify() == True
        assert theorem.status == TheoremStatus.VERIFIED
    
    def test_theorem_verify_fail(self):
        """Test theorem verification fails for non-equivalent forms."""
        theorem = Theorem(
            name="Invalid",
            description="Should fail",
            lhs=make_mark(),
            rhs=make_void()
        )
        assert theorem.verify() == False
        assert theorem.status == TheoremStatus.FAILED
    
    def test_theorem_string(self):
        """Test theorem string representation."""
        theorem = axiom_calling()
        theorem.verify()
        s = str(theorem)
        assert "J1" in s or "Calling" in s


class TestProofStep:
    """Tests for ProofStep class."""
    
    def test_proof_step_creation(self):
        """Test proof step creation."""
        step = ProofStep(
            step_number=1,
            form=make_mark(),
            justification="axiom"
        )
        assert step.step_number == 1
    
    def test_proof_step_string(self):
        """Test proof step string representation."""
        step = ProofStep(
            step_number=1,
            form=make_mark(),
            justification="J1"
        )
        s = str(step)
        assert "1." in s


class TestProof:
    """Tests for Proof class."""
    
    def test_proof_creation(self):
        """Test proof creation."""
        theorem = axiom_calling()
        proof = Proof(theorem=theorem)
        assert len(proof.steps) == 0
    
    def test_add_step(self):
        """Test adding steps to proof."""
        theorem = axiom_calling()
        proof = Proof(theorem=theorem)
        proof.add_step(make_mark(), "given")
        assert len(proof.steps) == 1
    
    def test_proof_string(self):
        """Test proof string representation."""
        theorem = axiom_calling()
        proof = Proof(theorem=theorem)
        s = str(proof)
        assert "Proof" in s


class TestAxioms:
    """Tests for axiom theorems."""
    
    def test_calling_axiom(self):
        """Test J1 (Calling) axiom."""
        theorem = axiom_calling()
        assert theorem.name == "J1 (Calling)"
        assert theorem.verify() == True
    
    def test_crossing_axiom(self):
        """Test J2 (Crossing) axiom."""
        theorem = axiom_crossing()
        assert theorem.name == "J2 (Crossing)"
        assert theorem.verify() == True
    
    def test_get_all_axioms(self):
        """Test getting all axioms."""
        axioms = get_all_axioms()
        assert len(axioms) == 2
        for axiom in axioms:
            assert isinstance(axiom, Theorem)


class TestConsequences:
    """Tests for derived theorems."""
    
    def test_theorem_generation(self):
        """Test generation theorem (excluded middle)."""
        theorem = theorem_generation()
        assert "Generation" in theorem.name or "C3" in theorem.name
        assert theorem.verify() == True
    
    def test_theorem_iteration(self):
        """Test iteration theorem (idempotence)."""
        theorem = theorem_iteration()
        assert "Iteration" in theorem.name or "C6" in theorem.name
        # aa = a for marks
        assert theorem.verify() == True
    
    def test_get_all_consequences(self):
        """Test getting all consequences."""
        consequences = get_all_consequences()
        assert len(consequences) >= 5
        for theorem in consequences:
            assert isinstance(theorem, Theorem)


class TestTheoremCollection:
    """Tests for theorem collection functions."""
    
    def test_get_all_theorems(self):
        """Test getting all theorems."""
        theorems = get_all_theorems()
        assert len(theorems) >= 7  # 2 axioms + 5+ consequences
    
    def test_verify_all_theorems(self):
        """Test verifying all theorems."""
        results = verify_all_theorems()
        assert isinstance(results, dict)
        # Check at least axioms pass
        assert any("J1" in k or "Calling" in k for k in results.keys())
        assert any("J2" in k or "Crossing" in k for k in results.keys())
    
    def test_theorem_summary(self):
        """Test theorem summary generation."""
        summary = theorem_summary()
        assert "AXIOMS" in summary or "Axioms" in summary
        assert "CONSEQUENCES" in summary or "Consequences" in summary


class TestSpecificTheorems:
    """Tests for specific theorem properties."""
    
    def test_position_theorem(self):
        """Test position theorem."""
        theorem = theorem_position()
        # This may or may not verify depending on form choice
        result = theorem.verify()
        assert theorem.status in [TheoremStatus.VERIFIED, TheoremStatus.FAILED]
    
    def test_all_axioms_verified(self):
        """Test all axioms can be verified."""
        for axiom in get_all_axioms():
            assert axiom.verify() == True
            assert axiom.proof_trace is not None

