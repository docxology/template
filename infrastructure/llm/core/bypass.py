"""Explicit allowlists for LLM sanitization and raw-query bypasses."""

from __future__ import annotations

from infrastructure.core.exceptions import SecurityError

# Keep this registry deliberately small. A caller must be named in source and
# provide a human-readable reason at every bypass site. Tests use a separate
# entry so they cannot accidentally certify a production caller.
SANITIZATION_BYPASS_CALLERS = {
    "infrastructure.llm.review.generation": "trusted internal review prompt assembled by the review pipeline",
    "tests.infra_tests.llm": "offline/local-server coverage of the raw protocol",
}
RAW_QUERY_BYPASS_CALLERS = {
    "tests.infra_tests.llm": "offline/local-server coverage of the raw protocol",
}


def _require(
    registry: dict[str, str],
    caller: str | None,
    reason: str | None,
    kind: str,
) -> None:
    """Require a registered caller and non-empty per-call rationale."""
    if not caller or caller not in registry:
        raise SecurityError(f"Unallowlisted {kind} bypass caller: {caller or '<missing>'}")
    if not reason or len(reason.strip()) < 12:
        raise SecurityError(f"{kind} bypass requires a named caller justification")


def require_sanitization_bypass(caller: str | None, reason: str | None) -> None:
    """Validate a caller opting out of normal prompt sanitization."""
    _require(SANITIZATION_BYPASS_CALLERS, caller, reason, "sanitization")


def require_raw_query_bypass(caller: str | None, reason: str | None) -> None:
    """Validate a caller using the low-level raw-query protocol."""
    _require(RAW_QUERY_BYPASS_CALLERS, caller, reason, "raw-query")


__all__ = [
    "RAW_QUERY_BYPASS_CALLERS",
    "SANITIZATION_BYPASS_CALLERS",
    "require_raw_query_bypass",
    "require_sanitization_bypass",
]
