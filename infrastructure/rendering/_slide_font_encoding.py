"""Metric-preserving Helvetica encoding for native slide readers.

ReportLab's WinAnsi codec chooses byte 127 for a bullet. Some native readers
leave that duplicate undefined, losing both Unicode text and glyph geometry.
These private fonts retain the standard Helvetica faces and metrics, encode
U+2022 at canonical WinAnsi byte 149, and publish the duplicate differences.
"""

from __future__ import annotations

from reportlab.pdfbase import pdfmetrics, rl_codecs

DECK_HELVETICA = "TemplateDeckHelvetica"
DECK_HELVETICA_BOLD = "TemplateDeckHelvetica-Bold"
DECK_HELVETICA_OBLIQUE = "TemplateDeckHelvetica-Oblique"
_ENCODING = "TemplateDeckEncoding"


def _register_slide_fonts() -> None:
    encoding = pdfmetrics.Encoding(_ENCODING, "WinAnsiEncoding")
    for code, glyph in enumerate(encoding.vector):
        if glyph == "bullet" and code != 149:
            encoding[code] = ".notdef"
    decoding: dict[int, int] = {}
    for code in range(256):
        try:
            character = bytes([code]).decode("winansi")
        except UnicodeDecodeError:
            continue
        if encoding[code] != ".notdef":
            decoding[code] = ord(character)
    encoding_map = {value: chr(value).encode("winansi")[0] for value in decoding.values()}
    encoding_map[ord("•")] = 149
    rl_codecs.RL_Codecs.add_dynamic_codec(_ENCODING, encoding_map, decoding)
    pdfmetrics.registerEncoding(encoding)
    for name, face in (
        (DECK_HELVETICA, "Helvetica"),
        (DECK_HELVETICA_BOLD, "Helvetica-Bold"),
        (DECK_HELVETICA_OBLIQUE, "Helvetica-Oblique"),
    ):
        pdfmetrics.registerFont(pdfmetrics.Font(name, face, _ENCODING))


_register_slide_fonts()
