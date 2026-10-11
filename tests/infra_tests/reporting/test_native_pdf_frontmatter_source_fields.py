"""Pure source-contract controls; these do not claim native PDF acceptance."""

from __future__ import annotations

import pytest

from infrastructure.reporting.native_format_pdf_frontmatter import compile_pdf_frontmatter_contract

SOURCE = b"""paper:
  title: Original Paper
  date: '2026-07-10'
authors:
  - name: Original Author
    affiliation: Original Institute
    email: original@example.test
    orcid: 0000-0001-6232-9096
publication:
  doi: 10.5281/zenodo.20533125
"""


def test_literal_original_orcid_doi_and_date_are_obligations() -> None:
    contract = compile_pdf_frontmatter_contract("source/config.yaml", SOURCE, "manuscript:pdf")
    by_id = {block.id: block.tokens for block in contract.blocks}
    assert by_id["config/authors/0/orcid"][0:2] == ("ORCID", ":")
    assert by_id["config/publication/doi"][0:2] == ("DOI", ":")
    assert by_id["config/date"] == ("2026", "-", "07", "-", "10")
    assert not contract.blockers


@pytest.mark.parametrize("section", ["paper", "book"])
def test_actual_configured_cover_key_remains_native_blocked(section: str) -> None:
    source = SOURCE + (f"{section}:\n  title: Cover Title\n  cover:\n    image: cover.png\n").encode()
    if section == "paper":
        source = SOURCE.replace(b"  title: Original Paper", b"  title: Original Paper\n  cover:\n    image: cover.png")
    contract = compile_pdf_frontmatter_contract("source/config.yaml", source, "manuscript:pdf")
    assert any(f"configured {section}/cover" in blocker for blocker in contract.blockers)


def test_missing_original_date_does_not_invent_runtime_today() -> None:
    source = SOURCE.replace(b"  date: '2026-07-10'\n", b"")
    assert source != SOURCE
    contract = compile_pdf_frontmatter_contract("source/config.yaml", source, "manuscript:pdf")
    assert all(block.id != "config/date" for block in contract.blocks)
    assert any("runtime clock" in blocker for blocker in contract.blockers)


def test_raw_title_date_retains_source_semantic_blocker() -> None:
    source = SOURCE.replace(b"'2026-07-10'", b"'\\today'")
    assert source != SOURCE
    contract = compile_pdf_frontmatter_contract("source/config.yaml", source, "manuscript:pdf")
    assert any("raw TeX" in blocker for blocker in contract.blockers)


def test_nonliteral_orcid_and_duplicate_original_key_are_refused() -> None:
    bad_orcid = SOURCE.replace(b"orcid: 0000-0001-6232-9096", b"orcid: [invented]")
    duplicate_title = SOURCE.replace(b"title: Original Paper", b"title: Original Paper\n  title: Forged Paper")
    assert bad_orcid != SOURCE and duplicate_title != SOURCE
    with pytest.raises(ValueError, match="literal text"):
        compile_pdf_frontmatter_contract("source/config.yaml", bad_orcid, "manuscript:pdf")
    with pytest.raises(ValueError, match="repeats a key"):
        compile_pdf_frontmatter_contract("source/config.yaml", duplicate_title, "manuscript:pdf")
