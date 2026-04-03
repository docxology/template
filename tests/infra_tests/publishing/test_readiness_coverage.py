"""Tests for infrastructure.publishing.readiness — comprehensive coverage."""


from infrastructure.publishing.readiness import validate_publication_readiness


class TestValidatePublicationReadiness:
    def test_complete_manuscript(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\n\nSummary of the paper.\n\n"
            "# Introduction\n\nBackground information.\n\n"
            "## Methodology\n\nOur approach uses...\n\n"
            "## Results\n\nWe found that...\n\n"
            "## Conclusion\n\nIn summary...\n\n"
            "\\cite{smith2020}\n"
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake content")

        result = validate_publication_readiness([md], [pdf])
        assert result["completeness_score"] == 85
        assert result["ready_for_publication"] is True
        assert "ready for publication" in result["recommendations"][-1].lower()

    def test_incomplete_manuscript(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("# Abstract\n\nJust an abstract.\n")

        result = validate_publication_readiness([md], [])
        assert result["completeness_score"] == 15
        assert result["ready_for_publication"] is False
        assert any("incomplete" in e.lower() for e in result["missing_elements"])
        assert any("No PDF" in e for e in result["missing_elements"])

    def test_no_citations_recommendation(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\nSummary\n"
            "# Introduction\nIntro\n"
            "## Methodology\nMethods\n"
            "## Results\nFindings\n"
            "## Conclusion\nConclusion\n"
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")

        result = validate_publication_readiness([md], [pdf])
        assert any("citations" in r.lower() for r in result["recommendations"])

    def test_no_figures_recommendation(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text("# Abstract\nText without figures.\n")
        result = validate_publication_readiness([md], [])
        assert any("figures" in r.lower() for r in result["recommendations"])

    def test_with_figures(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\nSummary\n\\includegraphics{fig1.png}\n"
        )
        result = validate_publication_readiness([md], [])
        # Should NOT recommend adding figures
        figure_recs = [r for r in result["recommendations"] if "figures" in r.lower()]
        assert len(figure_recs) == 0

    def test_unreadable_file(self, tmp_path):
        bad = tmp_path / "bad.md"
        bad.write_bytes(b"\xff\xfe\x80\x81")
        result = validate_publication_readiness([bad], [])
        assert len(result["skipped_files"]) == 1

    def test_empty_files(self, tmp_path):
        result = validate_publication_readiness([], [])
        assert result["completeness_score"] == 0
        assert result["ready_for_publication"] is False

    def test_alternative_section_names(self, tmp_path):
        md = tmp_path / "paper.md"
        md.write_text(
            "# Abstract\nSummary\n"
            "# Introduction\nIntro\n"
            "## Approach\nOur approach\n"
            "## Evaluation\nEvaluation results\n"
            "## Discussion\nDiscussion\n"
        )
        pdf = tmp_path / "out.pdf"
        pdf.write_bytes(b"%PDF")

        result = validate_publication_readiness([md], [pdf])
        assert result["completeness_score"] == 85

    def test_multiple_markdown_files(self, tmp_path):
        (tmp_path / "01_abstract.md").write_text("# Abstract\nSummary\n")
        (tmp_path / "02_intro.md").write_text("# Introduction\nIntro\n")
        (tmp_path / "03_methods.md").write_text("## Methods\nMethods\n")
        (tmp_path / "04_results.md").write_text("## Results\nResults\n")
        (tmp_path / "05_conclusion.md").write_text("## Summary\nSummary\n")

        files = sorted(tmp_path.glob("*.md"))
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")

        result = validate_publication_readiness(files, [pdf])
        assert result["completeness_score"] == 85
        assert result["ready_for_publication"] is True
