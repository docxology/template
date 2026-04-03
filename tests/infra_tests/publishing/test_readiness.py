"""Tests for infrastructure.publishing.readiness — comprehensive coverage."""


from infrastructure.publishing.readiness import validate_publication_readiness


def _write_manuscript(tmp_path, content):
    f = tmp_path / "manuscript.md"
    f.write_text(content)
    return [f]


class TestValidatePublicationReadiness:
    def test_complete_manuscript(self, tmp_path):
        content = (
            "# Abstract\n\nThis paper explores...\n\n"
            "# Introduction\n\nWe introduce...\n\n"
            "# Methodology\n\nOur approach...\n\n"
            "# Results\n\nWe found...\n\n"
            "# Conclusion\n\nIn summary...\n\n"
            "# References\n\n@article{smith2020}\n"
        )
        md_files = _write_manuscript(tmp_path, content)
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4")
        result = validate_publication_readiness(md_files, [pdf])
        assert result["completeness_score"] >= 85
        assert result["ready_for_publication"] is True

    def test_missing_sections(self, tmp_path):
        content = "# Abstract\n\nSome text.\n"
        md_files = _write_manuscript(tmp_path, content)
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")
        result = validate_publication_readiness(md_files, [pdf])
        assert result["completeness_score"] < 80
        assert result["ready_for_publication"] is False
        assert any("incomplete" in m.lower() for m in result["missing_elements"])

    def test_no_pdfs(self, tmp_path):
        content = "# Abstract\n\n# Introduction\n\n# Methodology\n\n# Results\n\n# Conclusion\n"
        md_files = _write_manuscript(tmp_path, content)
        result = validate_publication_readiness(md_files, [])
        assert result["ready_for_publication"] is False
        assert any("PDF" in m for m in result["missing_elements"])

    def test_no_citations_recommendation(self, tmp_path):
        content = "# Abstract\n\nPlain text without citations.\n"
        md_files = _write_manuscript(tmp_path, content)
        result = validate_publication_readiness(md_files, [])
        assert any("citation" in r.lower() for r in result["recommendations"])

    def test_no_figures_recommendation(self, tmp_path):
        content = "# Abstract\n\nNo figures here.\n"
        md_files = _write_manuscript(tmp_path, content)
        result = validate_publication_readiness(md_files, [])
        assert any("figure" in r.lower() for r in result["recommendations"])

    def test_empty_files(self, tmp_path):
        result = validate_publication_readiness([], [])
        assert result["completeness_score"] == 0
        assert result["ready_for_publication"] is False

    def test_methods_alternative_heading(self, tmp_path):
        content = "# Abstract\n\n# Introduction\n\n# Approach\n\n# Evaluation\n\n# Discussion\n"
        md_files = _write_manuscript(tmp_path, content)
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")
        result = validate_publication_readiness(md_files, [pdf])
        assert result["completeness_score"] >= 85

    def test_multiple_md_files(self, tmp_path):
        (tmp_path / "01_abstract.md").write_text("# Abstract\n\nSome abstract.\n")
        (tmp_path / "02_intro.md").write_text("# Introduction\n\nIntro text.\n")
        (tmp_path / "03_methods.md").write_text("# Methods\n\nApproach.\n")
        (tmp_path / "04_results.md").write_text("# Results\n\nFindings.\n")
        (tmp_path / "05_conclusion.md").write_text("# Conclusion\n\nEnd.\n")
        md_files = sorted(tmp_path.glob("*.md"))
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")
        result = validate_publication_readiness(md_files, [pdf])
        assert result["completeness_score"] >= 85

    def test_skipped_unreadable_files(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_bytes(b"\xff\xfe invalid utf8 \x80\x81")
        result = validate_publication_readiness([f], [])
        # Should not crash; file may or may not be skipped depending on encoding handling
        assert isinstance(result, dict)

    def test_ready_project_recommendation(self, tmp_path):
        content = "# Abstract\n\n# Introduction\n\n# Methodology\n\n# Results\n\n# Conclusion\n"
        md_files = _write_manuscript(tmp_path, content)
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF")
        result = validate_publication_readiness(md_files, [pdf])
        assert any("ready" in r.lower() for r in result["recommendations"])
