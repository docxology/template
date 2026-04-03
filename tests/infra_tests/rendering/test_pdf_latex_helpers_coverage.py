"""Tests for infrastructure.rendering._pdf_latex_helpers — comprehensive coverage."""


from infrastructure.rendering._pdf_latex_helpers import (
    extract_preamble,
    check_latex_log_for_graphics_errors,
    generate_title_page_preamble,
    generate_title_page_body,
    parse_missing_latex_package_from_log,
)


class TestExtractPreamble:
    def test_single_latex_block(self, tmp_path):
        f = tmp_path / "preamble.md"
        f.write_text("# Preamble\n\n```latex\n\\usepackage{amsmath}\n```\n")
        result = extract_preamble(f)
        assert "\\usepackage{amsmath}" in result

    def test_multiple_latex_blocks(self, tmp_path):
        f = tmp_path / "preamble.md"
        f.write_text(
            "```latex\n\\usepackage{amsmath}\n```\n\n"
            "```latex\n\\usepackage{graphicx}\n```\n"
        )
        result = extract_preamble(f)
        assert "amsmath" in result
        assert "graphicx" in result

    def test_no_latex_blocks(self, tmp_path):
        f = tmp_path / "preamble.md"
        f.write_text("# Just markdown\nNo latex here.\n")
        result = extract_preamble(f)
        assert result == ""

    def test_nonexistent_file(self, tmp_path):
        result = extract_preamble(tmp_path / "missing.md")
        assert result == ""

    def test_unreadable_file(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_bytes(b"\xff\xfe" + b"\x80" * 100)
        result = extract_preamble(f)
        # Either returns empty or handles gracefully
        assert isinstance(result, str)


class TestCheckLatexLogForGraphicsErrors:
    def test_no_errors(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("This is fine, no issues.\n")
        result = check_latex_log_for_graphics_errors(log)
        assert len(result["graphics_errors"]) == 0
        assert len(result["missing_files"]) == 0

    def test_missing_file(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("File `figure1.png` not found\n")
        result = check_latex_log_for_graphics_errors(log)
        assert "figure1.png" in result["missing_files"]

    def test_includegraphics_undefined(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("\\includegraphics Undefined control sequence\n")
        result = check_latex_log_for_graphics_errors(log)
        assert len(result["graphics_errors"]) == 1
        assert "graphicx" in result["graphics_errors"][0]

    def test_nonexistent_log(self, tmp_path):
        result = check_latex_log_for_graphics_errors(tmp_path / "missing.log")
        assert result["graphics_errors"] == []
        assert result["missing_files"] == []

    def test_graphics_warning(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("Package graphics Warning: something wrong\n\n")
        result = check_latex_log_for_graphics_errors(log)
        assert len(result["graphics_warnings"]) >= 1


class TestGenerateTitlePagePreamble:
    def test_basic_config(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text(
            "paper:\n"
            "  title: My Research Paper\n"
            "authors:\n"
            "  - name: Alice Smith\n"
            "    email: alice@example.com\n"
            "    affiliation: MIT\n"
            "    orcid: 0000-0001-2345-6789\n"
        )
        result = generate_title_page_preamble(tmp_path)
        assert "\\title{My Research Paper}" in result
        assert "Alice Smith" in result
        assert "alice@example.com" in result
        assert "MIT" in result
        assert "0000-0001-2345-6789" in result

    def test_with_subtitle(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text(
            "paper:\n"
            "  title: Main Title\n"
            "  subtitle: A Subtitle\n"
        )
        result = generate_title_page_preamble(tmp_path)
        assert "Main Title" in result
        assert "A Subtitle" in result

    def test_with_doi_and_date(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text(
            "paper:\n"
            "  title: Test\n"
            "  date: 2024-01-01\n"
            "publication:\n"
            "  doi: 10.1234/test\n"
            "authors:\n"
            "  - name: Bob\n"
        )
        result = generate_title_page_preamble(tmp_path)
        assert "10.1234/test" in result
        assert "2024-01-01" in result

    def test_no_config(self, tmp_path):
        result = generate_title_page_preamble(tmp_path)
        assert result == ""

    def test_empty_config(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("")
        result = generate_title_page_preamble(tmp_path)
        assert result == ""

    def test_no_date_uses_today(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: Test\n")
        result = generate_title_page_preamble(tmp_path)
        assert "\\today" in result

    def test_multiple_authors(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text(
            "paper:\n"
            "  title: Test\n"
            "authors:\n"
            "  - name: Alice\n"
            "  - name: Bob\n"
        )
        result = generate_title_page_preamble(tmp_path)
        assert "Alice" in result
        assert "Bob" in result
        assert "\\and" in result

    def test_author_without_name_skipped(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text(
            "paper:\n"
            "  title: Test\n"
            "authors:\n"
            "  - email: nobody@example.com\n"
            "  - name: Valid Author\n"
        )
        result = generate_title_page_preamble(tmp_path)
        assert "Valid Author" in result
        assert "nobody@example.com" not in result


class TestGenerateTitlePageBody:
    def test_basic(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: Test\n")
        result = generate_title_page_body(tmp_path)
        assert "\\maketitle" in result
        assert "\\thispagestyle{empty}" in result

    def test_no_config(self, tmp_path):
        result = generate_title_page_body(tmp_path)
        assert result == ""

    def test_empty_config(self, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("")
        result = generate_title_page_body(tmp_path)
        assert result == ""


class TestParseMissingLatexPackage:
    def test_sty_not_found(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("File `multirow.sty' not found\n")
        result = parse_missing_latex_package_from_log(log)
        assert result == "multirow"

    def test_latex_error_sty(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("! LaTeX Error: File `cleveref.sty' not found\n")
        result = parse_missing_latex_package_from_log(log)
        assert result == "cleveref"

    def test_no_missing_package(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("All good, no errors.\n")
        result = parse_missing_latex_package_from_log(log)
        assert result is None

    def test_nonexistent_log(self, tmp_path):
        result = parse_missing_latex_package_from_log(tmp_path / "missing.log")
        assert result is None


class TestErrorPaths:
    """Test error handler paths for code coverage."""

    def test_check_latex_log_unreadable(self, tmp_path):
        """check_latex_log_for_graphics_errors with unreadable file (OSError path)."""
        import stat

        log = tmp_path / "test.log"
        log.write_text("File `figure.png` not found\n")
        log.chmod(0o000)
        try:
            result = check_latex_log_for_graphics_errors(log)
            # Should return empty result on OSError
            assert isinstance(result, dict)
        finally:
            log.chmod(stat.S_IRWXU)

    def test_generate_title_page_preamble_invalid_yaml(self, tmp_path):
        """generate_title_page_preamble with invalid YAML (YAMLError path)."""
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: [\n  invalid yaml\n")
        result = generate_title_page_preamble(tmp_path)
        assert result == ""

    def test_generate_title_page_body_invalid_yaml(self, tmp_path):
        """generate_title_page_body with invalid YAML (YAMLError path)."""
        config = tmp_path / "config.yaml"
        config.write_text("paper:\n  title: [\n  broken\n")
        result = generate_title_page_body(tmp_path)
        assert result == ""

    def test_parse_missing_latex_package_unreadable(self, tmp_path):
        """parse_missing_latex_package_from_log with unreadable file (OSError path)."""
        import stat

        log = tmp_path / "test.log"
        log.write_text("File `multirow.sty' not found\n")
        log.chmod(0o000)
        try:
            result = parse_missing_latex_package_from_log(log)
            # Should return None on OSError
            assert result is None
        finally:
            log.chmod(stat.S_IRWXU)
