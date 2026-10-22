"""Typography contract for the dense PDF build.

These guard the config-driven typography invariants against silent re-breakage
by the repo's convergent automation (which re-authors files toward green). They
are source-level contracts — cheap, no render, no mocks — pinning exactly the
failure modes observed while wiring smaller font + tiny margins + red links:

* the preamble must be a fenced ```latex block (an unfenced preamble is recovered
  only by a whitelist fallback and should not be relied on here);
* the font scaling must use ``\\changefontsize[<baselineskip>]{<size>}`` — the
  baselineskip is the OPTIONAL bracketed arg. The double-brace form
  ``\\changefontsize{9pt}{11pt}`` silently prints the second brace as body text
  (a stray "11pt" leaked onto page 1 before this was caught);
* margins are config-driven (``config.yaml`` ``metadata.geometry``) and must be
  declared in exactly one place — the preamble must NOT also load ``\\geometry``
  or the two declarations clash.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREAMBLE = PROJECT_ROOT / "manuscript" / "preamble.md"
CONFIG = PROJECT_ROOT / "manuscript" / "config.yaml"


def _fenced_latex(preamble_text: str) -> str:
    blocks = re.findall(r"```\s*latex\s*\n(.*?)\n\s*```", preamble_text, re.DOTALL)
    return "\n".join(blocks)


def test_preamble_is_fenced() -> None:
    """The preamble ships a ```latex fence (not raw, drop-prone LaTeX)."""
    assert _fenced_latex(PREAMBLE.read_text()), "preamble.md must contain a ```latex fenced block"


def test_changefontsize_uses_bracketed_baselineskip() -> None:
    """Font scaling uses the bracketed optional-baselineskip form (no leaked token).

    Pins the exact arg-order bug: the double-brace form prints the second arg as
    body text, so it must never appear.
    """
    latex = _fenced_latex(PREAMBLE.read_text())
    assert "\\changefontsize" in latex, "expected \\changefontsize for dense body font"
    # Correct: \changefontsize[11pt]{9pt}
    assert re.search(r"\\changefontsize\[[^\]]+\]\{[^}]+\}", latex), (
        "\\changefontsize must use the [baselineskip]{size} bracketed form"
    )
    # Incorrect: \changefontsize{..}{..} leaks the second brace as a body token.
    # Allow intervening whitespace so a spaced double-brace cannot slip past.
    assert not re.search(r"\\changefontsize\s*\{[^}]+\}\s*\{[^}]+\}", latex), (
        "double-brace \\changefontsize{..}{..} leaks a stray token onto the page"
    )


def test_margins_are_config_driven_single_source() -> None:
    """Margins live in config metadata.geometry; the preamble must not also set them."""
    config = yaml.safe_load(CONFIG.read_text())
    geometry = (config.get("metadata") or {}).get("geometry")
    assert geometry, "config.yaml metadata.geometry must declare page margins"
    assert "margin" in geometry, f"unexpected geometry value: {geometry!r}"

    latex = _fenced_latex(PREAMBLE.read_text())
    assert "\\geometry" not in latex, "preamble must NOT declare \\geometry (config owns margins)"
    assert "{geometry}" not in latex, "preamble must NOT load the geometry package (pandoc loads it)"
