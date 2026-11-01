"""Required real PDF legacy control; pure reconstruction remains in smoke."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.infra_tests.reporting.test_paper_frontmatter_reconstruction import _project


@pytest.mark.timeout(90)
def test_real_public_pdf_without_frontmatter_retains_legacy_body(tmp_path: Path) -> None:
    from pypdf import PdfReader

    m, _, manager = _project(tmp_path, frontmatter=False)
    manager.config.pdf_dir = str(tmp_path / "output/pdf")
    source = m / "00_abstract.md"
    output = manager.render_combined_pdf([source], m, "legacy_fixture")
    assert "Development fixture." in "\n".join(page.extract_text() for page in PdfReader(output).pages)
    assert (output.parent / "_combined_manuscript.md").read_text() == source.read_text()
    assert "template-paper-frontmatter" not in (output.parent / "_combined_manuscript.tex").read_text()
