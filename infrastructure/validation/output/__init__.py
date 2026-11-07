"""Output validation providers, resolved on first use without leaf-import cycles."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

_EXPORTS = {
    "ValidationResultDict": (".validator", "ValidationResultDict"),
    "claim_verification_enabled": (".claim_verification", "claim_verification_enabled"),
    "collect_detailed_validation_results": (".validator", "collect_detailed_validation_results"),
    "scan_lexical_mock_policy": (".no_mock_enforcer", "scan_lexical_mock_policy"),
    "validate_claim_verification": (".claim_verification", "validate_claim_verification"),
    "validate_copied_outputs": (".validator", "validate_copied_outputs"),
    "validate_output_structure": (".validator", "validate_output_structure"),
    "validate_root_output_structure": (".validator", "validate_root_output_structure"),
    "verify_project_claims": (".claim_verification", "verify_project_claims"),
}

if TYPE_CHECKING:
    from .claim_verification import (
        claim_verification_enabled,
        validate_claim_verification,
        verify_project_claims,
    )
    from .no_mock_enforcer import scan_lexical_mock_policy
    from .validator import (
        ValidationResultDict,
        collect_detailed_validation_results,
        validate_copied_outputs,
        validate_output_structure,
        validate_root_output_structure,
    )

__all__ = [
    "ValidationResultDict",
    "collect_detailed_validation_results",
    "validate_copied_outputs",
    "claim_verification_enabled",
    "scan_lexical_mock_policy",
    "verify_project_claims",
    "validate_claim_verification",
    "validate_output_structure",
    "validate_root_output_structure",
]


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXPORTS.keys())
