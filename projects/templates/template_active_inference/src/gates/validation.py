"""Project-local validation gates (facade)."""

from __future__ import annotations

from gates.claim_ledger import validate_claim_ledger, verify_claim_bindings
from gates.lean import build_lean, lean_axioms_clean, lean_project_present
from gates.manuscript_checks import validate_manuscript
from gates.output_checks import validate_outputs

__all__ = [
    "build_lean",
    "lean_axioms_clean",
    "lean_project_present",
    "validate_claim_ledger",
    "validate_manuscript",
    "validate_outputs",
    "verify_claim_bindings",
]
