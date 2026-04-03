"""Tests for infrastructure.publishing.readiness — expanded coverage."""


from infrastructure.publishing.readiness import validate_publication_readiness


class TestValidatePublicationReadiness:
    def test_fully_ready(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\n\nThis paper...\n\n"
            "# Introduction\n\nWe introduce...\n\n"
            "# Methodology\n\nOur approach...\n\n"
            "# Results\n\nWe found...\n\n"
            "# Conclusion\n\nWe conclude...\n\n"
            "See \\cite{ref2020} for details.\n"
            "\\includegraphics{fig1.png}\n"
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF content")

        result = validate_publication_readiness([md], [pdf])
        assert result["completeness_score"] == 85  # 15+15+20+20+15
        assert result["ready_for_publication"] is True
        assert "ready for publication" in result["recommendations"][-1].lower()

    def test_missing_sections(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("# Introduction\n\nJust intro.\n")
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF content")

        result = validate_publication_readiness([md], [pdf])
        assert result["completeness_score"] == 15
        assert result["ready_for_publication"] is False
        assert "structure incomplete" in str(result["missing_elements"]).lower()

    def test_no_pdfs(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\n\n# Introduction\n\n# Methods\n\n"
            "# Results\n\n# Conclusion\n\n"
        )
        result = validate_publication_readiness([md], [])
        assert result["ready_for_publication"] is False
        assert any("PDF" in e for e in result["missing_elements"])

    def test_no_citations_recommendation(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\n\nSummary\n\n"
            "# Introduction\n\nIntro\n\n"
            "# Methods\n\nApproach\n\n"
            "# Results\n\nFindings\n\n"
            "# Conclusion\n\nEnd\n\n"
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF content")

        result = validate_publication_readiness([md], [pdf])
        assert any("citation" in r.lower() for r in result["recommendations"])

    def test_no_figures_recommendation(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\n\nSummary\n\n"
            "# Introduction\n\nIntro\n\n"
            "# Methodology\n\nApproach\n\n"
            "# Results\n\nFindings\n\n"
            "# Conclusion\n\nEnd\n\n"
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF content")

        result = validate_publication_readiness([md], [pdf])
        assert any("figure" in r.lower() for r in result["recommendations"])

    def test_empty_markdown(self, tmp_path):
        result = validate_publication_readiness([], [])
        assert result["completeness_score"] == 0
        assert result["ready_for_publication"] is False

    def test_unreadable_file(self, tmp_path):
        md = tmp_path / "bad.md"
        md.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8
        result = validate_publication_readiness([md], [])
        assert str(md) in str(result["skipped_files"])

    def test_alternative_section_names(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\n\nSummary\n\n"
            "# Introduction\n\nIntro\n\n"
            "# Approach\n\nOur method\n\n"
            "# Evaluation\n\nResults\n\n"
            "# Discussion\n\nConclusions\n\n"
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF content")

        result = validate_publication_readiness([md], [pdf])
        assert result["completeness_score"] == 85

    def test_multiple_markdown_files(self, tmp_path):
        (tmp_path / "01_abstract.md").write_text("# Abstract\n\nSummary\n")
        (tmp_path / "02_intro.md").write_text("# Introduction\n\nIntro\n")
        (tmp_path / "03_methods.md").write_text("# Methods\n\nApproach\n")
        (tmp_path / "04_results.md").write_text("# Results\n\nFindings\n")
        (tmp_path / "05_conclusion.md").write_text("# Conclusion\n\nEnd\n")
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF content")

        md_files = sorted(tmp_path.glob("*.md"))
        result = validate_publication_readiness(md_files, [pdf])
        assert result["completeness_score"] == 85
