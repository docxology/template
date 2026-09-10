"""TOC/cover injection after the begin-transmission bookend tests (split from test_transmission_validation.py)."""

from __future__ import annotations

from infrastructure.rendering._pdf_combined_transmission import _inject_toc_after_begin_transmission


class TestInjectTocAfterBeginTransmission:
    """Cover/TOC relocation after the begin-transmission bookend."""

    BASE_TEX = (
        "\\documentclass{article}\n\\begin{document}\n"
        "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
        "Bookend body\n\\end{samepage}\n\\newpage\n"
        "\\section{Abstract}\nBody\n\\end{document}"
    )

    def test_inserts_toc_and_cover_after_begin_bookend(self) -> None:
        """When title_page_body is provided, both cover and TOC are inserted."""
        result = _inject_toc_after_begin_transmission(
            self.BASE_TEX,
            begin_doc_idx=self.BASE_TEX.find("\\begin{document}"),
            title_page_body="\\maketitle",
        )
        toc_idx = result.find("\\tableofcontents")
        newpage_idx = result.find("\\newpage")
        abstract_idx = result.find("\\section{Abstract}")
        assert toc_idx > newpage_idx
        assert abstract_idx > toc_idx
        assert "\\maketitle" in result

    def test_inserts_only_toc_when_no_title_body(self) -> None:
        """Empty title_page_body skips cover and inserts only TOC."""
        result = _inject_toc_after_begin_transmission(
            self.BASE_TEX,
            begin_doc_idx=self.BASE_TEX.find("\\begin{document}"),
            title_page_body="",
        )
        assert "\\tableofcontents" in result
        assert "\\maketitle" not in result

    def test_returns_unchanged_when_label_not_found(self) -> None:
        """Missing begin-transmission label returns tex unchanged."""
        tex = "\\begin{document}\n\\section{No label}\nBody\n\\end{document}"
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
        )
        assert result == tex

    def test_returns_unchanged_when_samepage_missing(self) -> None:
        """Missing ``\\end{samepage}`` after the label returns tex unchanged."""
        tex = (
            "\\begin{document}\n"
            "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
            "Bookend body\n\\newpage\n"
            "\\section{Abstract}\nBody\n\\end{document}"
        )
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
        )
        assert result == tex

    def test_returns_unchanged_when_newpage_missing(self) -> None:
        """Missing ``\\newpage`` after samepage returns tex unchanged."""
        tex = (
            "\\begin{document}\n"
            "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
            "Bookend body\n\\end{samepage}\n"
            "\\section{Abstract}\nBody\n\\end{document}"
        )
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
        )
        assert result == tex

    def test_returns_unchanged_when_toc_already_present(self) -> None:
        """If ``\\tableofcontents`` is already in the window, no double-insert."""
        tex = (
            "\\begin{document}\n"
            "\\section{BEGINNING OF TRANSMISSION}\\label{beginning-of-transmission}\n"
            "Bookend body\n\\end{samepage}\n\\newpage\n"
            "\\tableofcontents\n\\newpage\n"
            "\\section{Abstract}\nBody\n\\end{document}"
        )
        result = _inject_toc_after_begin_transmission(
            tex,
            begin_doc_idx=tex.find("\\begin{document}"),
            title_page_body="\\maketitle",
        )
        assert result.count("\\tableofcontents") == 1
        assert "\\maketitle" not in result
