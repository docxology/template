"""Mermaid content invariant: reserved slot values must not leak into emitted content."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.grammar import RESERVED_SLOTS, load_grammar

PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_mermaid_blocks(md_file: Path) -> list[str]:
    """Extract content inside ```mermaid ... ``` fences."""
    text = md_file.read_text()
    blocks = re.findall(r"```mermaid(.*?)```", text, re.DOTALL)
    return blocks


def _all_manuscript_mds() -> list[Path]:
    ms_dir = PROJECT_ROOT / "manuscript"
    return sorted(ms_dir.glob("*.md"))


# ---------------------------------------------------------------------------
# Reserved slot values must not appear in Mermaid diagrams as data values
# (They can appear in comments or as labels, but not as raw slot option values
#  driving behavior)
# ---------------------------------------------------------------------------


RESERVED_SLOT_OPTIONS = {
    "figure_profile": ["mermaid_only", "mermaid_plus_plots", "full"],
    "qr_profile": ["figure", "page", "both", "full_encode"],
    "integrity_profile": ["sha256", "sha256_512", "sha512_merkle", "merkle_kmyth"],
}


def test_manuscript_mds_exist():
    mds = _all_manuscript_mds()
    assert len(mds) >= 5, f"Expected ≥5 manuscript md files, got {len(mds)}"


def test_mermaid_blocks_present():
    mds = _all_manuscript_mds()
    all_blocks = []
    for md in mds:
        all_blocks.extend(_load_mermaid_blocks(md))
    assert len(all_blocks) >= 3, "Expected at least 3 mermaid diagrams across manuscript"


@pytest.mark.parametrize(
    "slot,options",
    [
        ("qr_profile", RESERVED_SLOT_OPTIONS["qr_profile"]),
        ("integrity_profile", RESERVED_SLOT_OPTIONS["integrity_profile"]),
    ],
)
def test_reserved_slot_options_not_in_mermaid(slot, options):
    """Reserved slot option strings should not appear as node labels in Mermaid blocks."""
    mds = _all_manuscript_mds()
    for md in mds:
        blocks = _load_mermaid_blocks(md)
        for block in blocks:
            for opt in options:
                # Check that the option is not used as a bracketed node label
                # e.g. [mermaid_only] would be suspicious
                pattern = rf"\[{re.escape(opt)}\]"
                assert not re.search(pattern, block), (
                    f"Reserved slot option '{opt}' for '{slot}' found as node label in Mermaid block in {md.name}"
                )


def test_grammar_reserved_slots_are_named():
    g = load_grammar(PROJECT_ROOT)
    reserved_names = {s.name for s in g.reserved_slots}
    for slot in RESERVED_SLOTS:
        assert slot in reserved_names


def test_grammar_loads_cleanly():
    g = load_grammar(PROJECT_ROOT)
    assert g.grammar_hash is not None
    assert len(g.grammar_hash) == 16
