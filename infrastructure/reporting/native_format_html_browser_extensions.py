"""Exact source-owned observer extensions for finite HTML fidelity evidence."""

from __future__ import annotations

from infrastructure.reporting.native_format_html_column_allocation import ALLOCATION_SCRIPT
from infrastructure.reporting.native_format_html_glyph_contours import GLYPH_STYLE_SCRIPT
from infrastructure.reporting.native_format_html_image_alt import ALT_SCRIPT
from infrastructure.reporting.native_format_html_integer_resampling import RESAMPLING_SCRIPT


def extend_browser_observer_script(script: str) -> str:
    """Append real native observations at two unique existing SDK anchors.

    The enclosing audit/replay must bind these exact source bytes as its observer
    identity. The extensions execute SDK code, never original SourceDATA. Native
    font usage additionally requires the bounded CDP helper before screenshot.
    """
    before = " const data={tables,footnotes,footnote_refs,config_metadata,math_leaf_census,"
    after = " const out=document.createElement('pre');out.id='native-browser-observation';"
    if script.count(before) != 1 or script.count(after) != 1:
        raise ValueError("native HTML SDK observer anchors changed; explicit integration required")
    return script.replace(before, GLYPH_STYLE_SCRIPT + ALLOCATION_SCRIPT + before).replace(
        after, ALT_SCRIPT + RESAMPLING_SCRIPT + after
    )
