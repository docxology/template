"""Bind genuinely observed Office font usage to held Source body/face bytes.

This body predicate grants no browser-origin, platform font selection, shaping,
complete native ink or operating-system authority. Those original gates remain.
"""

from __future__ import annotations

from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_mermaid_font_bodies import NativeMermaidFontBodies


def verify_actual_office_mermaid_fonts(
    reference: dict[str, Any], owner: NativeMermaidFontBodies, *, deadline: float
) -> None:
    """Use only the actual observer's reference while its Source owner lives.

    The Source-owned caller separately authenticates the actual observer and
    process graph. Passed usage labels alone cannot establish that origin.
    """
    remaining(deadline)
    if not isinstance(owner, NativeMermaidFontBodies):
        raise ValueError("Office font bodies require the genuine typed current Source owner")
    owner.verify_live(deadline=deadline)
    for occurrence in reference["occurrences"]:
        remaining(deadline)
        fonts = occurrence["paint"]["fonts"]
        owner.authenticate_retained_fonts(fonts, deadline=deadline)
    owner.verify_terminal_bytes(deadline=deadline)
    remaining(deadline)
