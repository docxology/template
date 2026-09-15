"""Stable, dotted IDs for formal-contract diagnostics.

Follows the same ``namespace.SCREAMING_SNAKE_CASE`` convention as
``infrastructure.validation.content.diagnostic_codes``. Adding a code is
non-breaking; changing or removing one is a breaking change for downstream
``jq``/``rg`` filters. These codes are NEW and orthogonal to the
``MARKDOWN.*`` / ``BIBTEX.*`` families.
"""


class FormalCode:
    """Stable IDs for findings emitted by ``compose`` and ``check_manuscript``."""

    DUPLICATE_ID = "FORMAL.DUPLICATE_ID"
    CYCLE_DETECTED = "FORMAL.CYCLE_DETECTED"
    DANGLING_EDGE = "FORMAL.DANGLING_EDGE"
    SECTION_CHILD_MISSING = "FORMAL.SECTION_CHILD_MISSING"
    DANGLING_REF = "FORMAL.DANGLING_REF"
    UNSUPPORTED_CLAIM = "FORMAL.UNSUPPORTED_CLAIM"
    INSUFFICIENT_TIER = "FORMAL.INSUFFICIENT_TIER"
    ORPHAN_BLOCK = "FORMAL.ORPHAN_BLOCK"
    READER_PARSE = "FORMAL.READER_PARSE"


__all__ = ["FormalCode"]
