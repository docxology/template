"""Composable private-project promotion contracts with compatible re-exports."""

from infrastructure.project.promotion.attestation import (
    ATTESTATION_CHECK_FIELDS,
    load_promotion_attestation,
    validate_promotion_attestation,
)
from infrastructure.project.promotion.cli import build_parser, main
from infrastructure.project.promotion.composite import evaluate_promotion_candidate
from infrastructure.project.promotion.models import (
    PromotionAttestation,
    PromotionCompositeReport,
    PromotionGateReport,
    SecurityTodoFinding,
)
from infrastructure.project.promotion.security_gate import (
    PROMOTION_CHECKS,
    check_private_project_promotion,
    render_promotion_report,
    scan_security_todos,
)

__all__ = [
    "ATTESTATION_CHECK_FIELDS",
    "PROMOTION_CHECKS",
    "PromotionAttestation",
    "PromotionCompositeReport",
    "PromotionGateReport",
    "SecurityTodoFinding",
    "build_parser",
    "check_private_project_promotion",
    "evaluate_promotion_candidate",
    "load_promotion_attestation",
    "main",
    "render_promotion_report",
    "scan_security_todos",
    "validate_promotion_attestation",
]
