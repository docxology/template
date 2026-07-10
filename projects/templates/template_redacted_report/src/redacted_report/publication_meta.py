"""Publication byline sourced from ``manuscript/config.yaml``.

The visual proof PDFs stamp authorship on every title page and into the
steganography metadata; sourcing it here keeps a single source of truth
(a hardcoded scaffold author shipped in every tracked proof PDF before
this). Both values are fixed strings from the config, so the proof
matrix's deterministic-bytes guarantee is preserved.
"""

from __future__ import annotations

from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "manuscript" / "config.yaml"


def publication_author_and_date() -> tuple[str, str]:
    """Return (author name, paper date) from the manuscript config."""
    try:
        import yaml

        data = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        authors = data.get("authors") or []
        name = str(authors[0].get("name", "")) if authors else ""
        date = str((data.get("paper") or {}).get("date", ""))
        return (name or "Template Author", date)
    except Exception:  # noqa: BLE001 - safety net: proof PDFs must still render standalone without a readable config; falls back to a neutral byline
        return ("Template Author", "")
