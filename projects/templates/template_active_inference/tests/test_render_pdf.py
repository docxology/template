"""Behavioral controls for the standalone renderer's preamble parsing.

Full Pandoc/XeLaTeX rendering remains a separate native acceptance requirement.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Add project src to path so manuscript.render_helpers resolves stand-alone.
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from manuscript.render_helpers import extract_preamble  # noqa: E402


def test_extract_preamble_reads_fenced_latex(tmp_path: Path) -> None:
    f = tmp_path / "preamble.md"
    f.write_text(
        "intro\n```latex\n  \\changefontsize[11pt]{9pt}  \n```\n"
        "prose stays out\n```python\nraise RuntimeError('not LaTeX')\n```\n"
        "```latex\n\\setlength{\\parindent}{0pt}\n```\n",
        encoding="utf-8",
    )
    assert extract_preamble(f) == "\\changefontsize[11pt]{9pt}\n\\setlength{\\parindent}{0pt}"


def test_extract_preamble_missing_returns_empty(tmp_path: Path) -> None:
    assert extract_preamble(tmp_path / "nope.md") == ""
