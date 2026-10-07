"""Real XeTeX position-record invariants, including repeated TOC math."""

from __future__ import annotations

import pytest

from infrastructure.reporting.native_format_pdf_positions import source_math_positions_from_aux

# Record shape and scaled-point values were observed from an actual XeTeX
# source-only compilation. Repeated IDs represent TOC/header paints, not loss.
_RECORDS = (
    b"\\NativeSourceMathPosition{M000000-start}{6991545}{37012602}{1}\n"
    b"\\NativeSourceMathPosition{M000000-end}{7695270}{37012602}{1}\n"
    b"\\NativeSourceMathPosition{M000000-start}{8482197}{47888223}{2}\n"
    b"\\NativeSourceMathPosition{M000000-end}{9438315}{47888223}{2}\n"
)
_BINDINGS = ({"identity": "blocks/0/c/2", "marker": "M000000", "mcid": 0},)


def test_repeated_source_math_positions_preserve_both_native_pages() -> None:
    rows = source_math_positions_from_aux(_RECORDS, _BINDINGS)
    assert [row["start_sp"][2] for row in rows] == [1, 2]
    assert {row["identity"] for row in rows} == {"blocks/0/c/2"}


def test_original_source_math_cannot_disappear_from_aux() -> None:
    with pytest.raises(ValueError, match="lost a source"):
        source_math_positions_from_aux(b"\\relax\n", _BINDINGS)


def test_unclosed_source_math_position_is_rejected() -> None:
    with pytest.raises(ValueError, match="lost a source"):
        source_math_positions_from_aux(_RECORDS.splitlines(keepends=True)[0], _BINDINGS)


def test_undeclared_native_math_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="undeclared"):
        source_math_positions_from_aux(_RECORDS.replace(b"M000000", b"M000001"), _BINDINGS)
