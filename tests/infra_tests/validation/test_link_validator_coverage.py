"""Tests for infrastructure.validation.integrity.link_validator — additional coverage."""

import sys

from infrastructure.validation.integrity.link_validator import LinkValidator, main


class TestResolveEdgeCases:
    def test_resolve_relative_dot_slash(self, tmp_path):
        (tmp_path / "other.md").write_text("# Other")
        source = tmp_path / "test.md"
        source.write_text("[link](./other.md)")

        validator = LinkValidator(tmp_path)
        resolved, is_external = validator.resolve_link_target("./other.md", source)
        assert resolved is not None
        assert is_external is False

    def test_resolve_ftp_external(self, tmp_path):
        validator = LinkValidator(tmp_path)
        resolved, is_external = validator.resolve_link_target(
            "ftp://files.example.com/data.tar.gz", tmp_path / "test.md"
        )
        assert resolved is None
        assert is_external is True

    def test_resolve_absolute_path_outside_repo(self, tmp_path):
        validator = LinkValidator(tmp_path)
        # ../../../ going way outside repo
        source = tmp_path / "test.md"
        resolved, is_external = validator.resolve_link_target(
            "../../../../../../etc/passwd", source
        )
        # Should resolve to None (outside repo)
        assert is_external is False

    def test_resolve_empty_after_anchor_strip(self, tmp_path):
        validator = LinkValidator(tmp_path)
        source = tmp_path / "test.md"
        source.write_text("content")
        resolved, is_external = validator.resolve_link_target("#section", source)
        assert resolved == source
        assert is_external is False

    def test_resolve_file_with_anchor_exists(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide\n## Section\n")
        validator = LinkValidator(tmp_path)
        source = tmp_path / "test.md"
        resolved, is_external = validator.resolve_link_target("guide.md#section", source)
        assert resolved is not None

    def test_resolve_file_with_anchor_missing(self, tmp_path):
        validator = LinkValidator(tmp_path)
        source = tmp_path / "test.md"
        resolved, is_external = validator.resolve_link_target("missing.md#section", source)
        assert resolved is None

    def test_resolve_directory_with_agents_md(self, tmp_path):
        sub = tmp_path / "infra"
        sub.mkdir()
        (sub / "AGENTS.md").write_text("# Agents")
        validator = LinkValidator(tmp_path)
        source = tmp_path / "test.md"
        resolved, is_external = validator.resolve_link_target("infra/", source)
        assert resolved is not None
        assert "AGENTS.md" in str(resolved)

    def test_resolve_directory_relative_to_source(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        inner = sub / "api"
        inner.mkdir()
        (inner / "README.md").write_text("# API")
        validator = LinkValidator(tmp_path)
        source = sub / "index.md"
        source.write_text("content")
        resolved, is_external = validator.resolve_link_target("api/", source)
        assert resolved is not None

    def test_resolve_nonexistent_directory(self, tmp_path):
        validator = LinkValidator(tmp_path)
        source = tmp_path / "test.md"
        resolved, is_external = validator.resolve_link_target("nonexistent_dir/", source)
        assert resolved is None


class TestValidateFileLinksEdgeCases:
    def test_internal_anchor_link_with_hash(self, tmp_path):
        (tmp_path / "other.md").write_text("# Other\n## Heading\n")
        test_file = tmp_path / "test.md"
        test_file.write_text("[link](other.md#heading)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_file_links(test_file)
        anchor_links = [l for l in results["valid"] if l["type"] == "internal_anchor"]
        assert len(anchor_links) == 1

    def test_broken_anchor_link(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("[link](missing.md#section)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_file_links(test_file)
        assert len(results["broken"]) == 1

    def test_directory_link_with_index(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "README.md").write_text("# Docs")
        test_file = tmp_path / "test.md"
        test_file.write_text("[Docs](docs/)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_file_links(test_file)
        dir_links = [l for l in results["valid"] if l["type"] == "directory_index"]
        assert len(dir_links) == 1

    def test_directory_link_exists_no_index(self, tmp_path):
        sub = tmp_path / "data"
        sub.mkdir()
        test_file = tmp_path / "test.md"
        test_file.write_text("[Data](data/)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_file_links(test_file)
        dir_links = [l for l in results["valid"] if l["type"] == "directory"]
        assert len(dir_links) == 1

    def test_directory_link_broken(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("[Missing](nonexistent/)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_file_links(test_file)
        assert len(results["broken"]) == 1

    def test_binary_file_unreadable(self, tmp_path):
        bad = tmp_path / "bad.md"
        bad.write_bytes(b"\xff\xfe\x80\x81\x90\x91")
        validator = LinkValidator(tmp_path)
        results = validator.validate_file_links(bad)
        assert results == {"valid": [], "broken": []}


class TestGenerateReport:
    def test_all_valid(self, tmp_path):
        (tmp_path / "a.md").write_text("[ext](https://example.com)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_all_markdown_files()
        report = validator.generate_report(results)
        assert "All Links Valid" in report

    def test_broken_links_table(self, tmp_path):
        (tmp_path / "a.md").write_text("[broken](missing.md)")
        validator = LinkValidator(tmp_path)
        results = validator.validate_all_markdown_files()
        report = validator.generate_report(results)
        assert "## Broken Links" in report
        assert "missing.md" in report


class TestMainFunction:
    def test_main_clean_repo(self, tmp_path, monkeypatch):
        (tmp_path / "test.md").write_text("[ext](https://example.com)")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["link_validator"])
        result = main()
        assert result == 0

    def test_main_broken_links(self, tmp_path, monkeypatch):
        (tmp_path / "test.md").write_text("[broken](missing.md)")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["link_validator"])
        result = main()
        assert result == 1

    def test_main_with_output_file(self, tmp_path, monkeypatch):
        (tmp_path / "test.md").write_text("[ext](https://example.com)")
        output_file = tmp_path / "report.md"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["link_validator", "--output", str(output_file)])
        result = main()
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Markdown Link Validation Report" in content
