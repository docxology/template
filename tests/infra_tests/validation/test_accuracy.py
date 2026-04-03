"""Tests for infrastructure.validation.docs.accuracy — comprehensive coverage."""


from infrastructure.validation.docs.accuracy import (
    extract_headings,
    resolve_file_path,
    check_links,
    extract_script_name,
    verify_commands,
    check_file_paths,
    validate_config_options,
    check_terminology,
    run_accuracy_phase,
)


# ---------------------------------------------------------------------------
# extract_headings
# ---------------------------------------------------------------------------


class TestExtractHeadings:
    def test_simple_headings(self):
        content = "# Hello World\n## Sub Section\n### Deep"
        headings = extract_headings(content)
        assert "hello-world" in headings
        assert "sub-section" in headings
        assert "deep" in headings

    def test_explicit_anchor(self):
        content = "## My Section {#custom-anchor}"
        headings = extract_headings(content)
        assert "custom-anchor" in headings

    def test_special_chars_stripped(self):
        content = "# What's New? (v2.0)"
        headings = extract_headings(content)
        # Special chars removed, spaces become dashes
        assert any("whats-new" in h for h in headings)

    def test_empty_content(self):
        assert extract_headings("") == set()

    def test_no_headings(self):
        content = "Just a paragraph.\nAnother line."
        assert extract_headings(content) == set()


# ---------------------------------------------------------------------------
# resolve_file_path
# ---------------------------------------------------------------------------


class TestResolveFilePath:
    def test_existing_file(self, tmp_path):
        (tmp_path / "readme.md").write_text("hi")
        source = tmp_path / "docs" / "guide.md"
        source.parent.mkdir(parents=True)
        source.write_text("x")
        exists, msg, ptype = resolve_file_path("../readme.md", source, tmp_path)
        assert exists is True
        assert ptype == "file"

    def test_nonexistent_file(self, tmp_path):
        source = tmp_path / "guide.md"
        source.write_text("x")
        exists, msg, ptype = resolve_file_path("missing.md", source, tmp_path)
        assert exists is False
        assert ptype == "file"

    def test_existing_directory(self, tmp_path):
        (tmp_path / "subdir").mkdir()
        source = tmp_path / "guide.md"
        source.write_text("x")
        exists, msg, ptype = resolve_file_path("subdir/", source, tmp_path)
        assert exists is True
        assert ptype == "directory"

    def test_relative_dot_path(self, tmp_path):
        (tmp_path / "sibling.md").write_text("hi")
        source = tmp_path / "guide.md"
        source.write_text("x")
        exists, msg, ptype = resolve_file_path("./sibling.md", source, tmp_path)
        assert exists is True

    def test_path_outside_repo(self, tmp_path):
        source = tmp_path / "guide.md"
        source.write_text("x")
        exists, msg, ptype = resolve_file_path("../../../../../../etc/passwd", source, tmp_path)
        assert exists is False
        assert "outside" in msg.lower() or "does not exist" in msg.lower()


# ---------------------------------------------------------------------------
# check_links
# ---------------------------------------------------------------------------


class TestCheckLinks:
    def test_valid_file_link(self, tmp_path):
        (tmp_path / "other.md").write_text("target")
        md = tmp_path / "doc.md"
        md.write_text("[link](other.md)")
        issues = check_links([md], tmp_path, {})
        assert issues == []

    def test_broken_file_link(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("[link](missing.md)")
        issues = check_links([md], tmp_path, {})
        assert len(issues) == 1
        assert issues[0].issue_type == "broken_file"

    def test_valid_anchor_link(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Hello\n[link](#hello)")
        headings = {str(md.relative_to(tmp_path)): {"hello"}}
        issues = check_links([md], tmp_path, headings)
        assert issues == []

    def test_broken_anchor_link(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Hello\n[link](#nonexistent)")
        headings = {str(md.relative_to(tmp_path)): {"hello"}}
        issues = check_links([md], tmp_path, headings)
        assert len(issues) == 1
        assert issues[0].issue_type == "broken_anchor"

    def test_http_links_ignored(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("[link](https://example.com)")
        issues = check_links([md], tmp_path, {})
        assert issues == []

    def test_links_in_code_blocks_skipped(self, tmp_path):
        md = tmp_path / "doc.md"
        content = "```\n[link](nonexistent.md)\n```"
        md.write_text(content)
        issues = check_links([md], tmp_path, {})
        assert issues == []


# ---------------------------------------------------------------------------
# extract_script_name
# ---------------------------------------------------------------------------


class TestExtractScriptName:
    def test_sh_script(self):
        assert extract_script_name("./run.sh") == "run.sh"

    def test_python_script(self):
        assert extract_script_name("python scripts/analyze.py") == "scripts/analyze.py"

    def test_python3_script(self):
        assert extract_script_name("python3 scripts/test.py --verbose") == "scripts/test.py"

    def test_no_script(self):
        assert extract_script_name("echo hello") is None

    def test_nested_path(self):
        assert extract_script_name("./scripts/deploy.sh") == "scripts/deploy.sh"


# ---------------------------------------------------------------------------
# verify_commands
# ---------------------------------------------------------------------------


class TestVerifyCommands:
    def test_existing_script(self, tmp_path):
        (tmp_path / "run.sh").write_text("#!/bin/bash\necho hi")
        md = tmp_path / "doc.md"
        md.write_text("```bash\n./run.sh\n```")
        issues = verify_commands([md], tmp_path)
        assert issues == []

    def test_missing_script(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("```bash\n./missing_script.sh\n```")
        issues = verify_commands([md], tmp_path)
        assert len(issues) == 1
        assert "missing_script.sh" in issues[0].message

    def test_comments_skipped(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("```bash\n# ./not_a_command.sh\n```")
        issues = verify_commands([md], tmp_path)
        assert issues == []


# ---------------------------------------------------------------------------
# check_file_paths
# ---------------------------------------------------------------------------


class TestCheckFilePaths:
    def test_existing_path(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "mod.py").write_text("x")
        md = tmp_path / "doc.md"
        md.write_text("See `src/mod.py` for details.")
        issues = check_file_paths([md], tmp_path)
        assert issues == []

    def test_missing_path(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("See `missing/file.py` for details.")
        issues = check_file_paths([md], tmp_path)
        assert len(issues) >= 1

    def test_output_paths_skipped(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("See `output/reports/results.json`")
        issues = check_file_paths([md], tmp_path)
        assert issues == []


# ---------------------------------------------------------------------------
# validate_config_options / check_terminology
# ---------------------------------------------------------------------------


class TestValidateConfigOptions:
    def test_no_config(self):
        issues = validate_config_options([], {})
        assert issues == []

    def test_with_config_yaml(self, tmp_path):
        cfg = tmp_path / "config.yaml"
        cfg.write_text("key: value\n")
        issues = validate_config_options([], {"config.yaml": cfg})
        assert issues == []


class TestCheckTerminology:
    def test_returns_empty(self):
        assert check_terminology([]) == []


# ---------------------------------------------------------------------------
# run_accuracy_phase
# ---------------------------------------------------------------------------


class TestRunAccuracyPhase:
    def test_basic_run(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Hello\nSome text.")
        report, link_issues, accuracy_issues, all_headings = run_accuracy_phase(
            [md], tmp_path, {}
        )
        assert "link_issues" in report
        assert "total_issues" in report
        assert isinstance(link_issues, list)
        assert isinstance(accuracy_issues, list)
        assert str(md.relative_to(tmp_path)) in all_headings

    def test_empty_file_list(self, tmp_path):
        report, link_issues, accuracy_issues, all_headings = run_accuracy_phase(
            [], tmp_path, {}
        )
        assert report["total_issues"] == 0
        assert all_headings == {}

    def test_detects_broken_links(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("[broken](nonexistent.md)")
        report, link_issues, accuracy_issues, all_headings = run_accuracy_phase(
            [md], tmp_path, {}
        )
        assert report["link_issues"] >= 1
        assert len(link_issues) >= 1
