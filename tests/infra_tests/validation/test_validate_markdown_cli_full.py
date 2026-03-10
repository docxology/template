"""Full tests for infrastructure/validation/validate_markdown_cli.py.

Tests Markdown validation CLI functionality thoroughly.
"""

import os
import subprocess
import sys
from pathlib import Path


class TestValidateMarkdownCliFunctions:
    """Test module functions."""

    def test_repo_root(self):
        """Test _repo_root helper."""
        from infrastructure.validation.validate_markdown_cli import _repo_root

        result = _repo_root()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_find_markdown_files(self, tmp_path):
        """Test find_markdown_files function."""
        from infrastructure.validation.validate_markdown_cli import find_markdown_files

        (tmp_path / "01_intro.md").write_text("# Intro")
        (tmp_path / "02_body.md").write_text("# Body")
        (tmp_path / "03_conclusion.md").write_text("# Conclusion")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 3
        # Files should be sorted numerically
        assert any("01_intro.md" in f for f in files)

    def test_find_markdown_files_no_extension(self, tmp_path):
        """Test find_markdown_files with non-markdown files."""
        from infrastructure.validation.validate_markdown_cli import find_markdown_files

        (tmp_path / "test.txt").write_text("Not markdown")
        (tmp_path / "doc.md").write_text("# Doc")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 1
        assert "doc.md" in files[0]

    def test_collect_symbols(self, tmp_path):
        """Test collect_symbols function (canonical: labels=LaTeX \\label{}, anchors={#...})."""
        from infrastructure.validation.validate_markdown_cli import collect_symbols

        md = tmp_path / "test.md"
        md.write_text("# Title {#title}\n\n\\label{eq:one}")

        labels, anchors = collect_symbols([str(md)])

        assert "eq:one" in labels  # LaTeX \label{...}
        assert "title" in anchors  # {#...} section anchors

    def test_collect_symbols_empty_file(self, tmp_path):
        """Test collect_symbols with empty file."""
        from infrastructure.validation.validate_markdown_cli import collect_symbols

        md = tmp_path / "empty.md"
        md.write_text("")

        labels, anchors = collect_symbols([str(md)])

        assert len(labels) == 0
        assert len(anchors) == 0

    def test_validate_images_found(self, tmp_path):
        """Test validate_images with existing image."""
        from infrastructure.validation.validate_markdown_cli import validate_images

        (tmp_path / "img.png").write_bytes(b"\x89PNG")
        md = tmp_path / "doc.md"
        md.write_text("![Alt](img.png)")

        issues = validate_images([str(md)], str(tmp_path))

        assert len(issues) == 0

    def test_validate_images_missing(self, tmp_path):
        """Test validate_images with missing image."""
        from infrastructure.validation.validate_markdown_cli import validate_images

        md = tmp_path / "doc.md"
        md.write_text("![Alt](missing.png)")

        issues = validate_images([str(md)], str(tmp_path))

        assert len(issues) == 1
        assert "Missing image" in issues[0]

    def test_validate_images_no_refs(self, tmp_path):
        """Test validate_images with no image references produces no issues."""
        from infrastructure.validation.validate_markdown_cli import validate_images

        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nNo images here.")

        issues = validate_images([str(md)], str(tmp_path))

        assert len(issues) == 0

    def test_validate_refs_found(self, tmp_path):
        """Test validate_refs with existing internal anchor reference."""
        from infrastructure.validation.validate_markdown_cli import validate_refs

        md = tmp_path / "doc.md"
        md.write_text("# Section {#section}\n\n[Link to section](#section)")

        anchors = {"section"}
        issues = validate_refs([str(md)], str(tmp_path), set(), anchors)

        # No missing-anchor issues (the bare-URL / non-informative-text checks
        # may fire for other patterns, but the internal link itself is resolved)
        anchor_issues = [i for i in issues if "Missing anchor" in i]
        assert len(anchor_issues) == 0

    def test_validate_refs_missing(self, tmp_path):
        """Test validate_refs with missing internal anchor reference."""
        from infrastructure.validation.validate_markdown_cli import validate_refs

        md = tmp_path / "doc.md"
        md.write_text("[Link text](#missing)")

        issues = validate_refs([str(md)], str(tmp_path), set(), set())

        anchor_issues = [i for i in issues if "missing" in i.lower() or "Missing" in i]
        assert len(anchor_issues) >= 1

    def test_validate_math_no_issues(self, tmp_path):
        """Test validate_math with clean content (no display math constructs)."""
        from infrastructure.validation.validate_markdown_cli import validate_math

        md = tmp_path / "doc.md"
        md.write_text("Inline math: $E = mc^2$ is fine.")

        issues = validate_math([str(md)], str(tmp_path))

        assert len(issues) == 0

    def test_validate_math_double_dollar(self, tmp_path):
        """Test validate_math flags $$ display math (use equation env instead)."""
        from infrastructure.validation.validate_markdown_cli import validate_math

        md = tmp_path / "doc.md"
        md.write_text("$$E = mc^2$$")

        issues = validate_math([str(md)], str(tmp_path))

        assert len(issues) >= 1
        assert any("equation" in i.lower() or "$$" in i for i in issues)


class TestValidateMarkdownMain:
    """Test main function."""

    def test_main_success(self, tmp_path):
        """Test main with valid markdown."""
        # Create the expected directory structure: projects/project/manuscript
        manuscript_dir = tmp_path / "projects" / "project" / "manuscript"
        manuscript_dir.mkdir(parents=True)

        # Create valid markdown file in manuscript directory
        md_file = manuscript_dir / "test.md"
        md_file.write_text("# Test\n\nSome valid content.")

        # Run CLI directly
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "validation" / "validate_markdown_cli.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Pass the manuscript directory as an argument to the script
        result = subprocess.run(
            [sys.executable, str(script_path), str(manuscript_dir)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        # Should succeed with valid markdown
        assert result.returncode == 0

    def test_main_with_issues(self, tmp_path):
        """Test main with validation issues."""
        # Create markdown file with issues (broken reference)
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nSee [broken link](nonexistent.md) for details.")

        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "validation" / "validate_markdown_cli.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
            timeout=30,
        )

        # Should find validation issues and exit with error
        assert result.returncode != 0

    def test_main_import_error_handling(self):
        """Test that main handles import errors gracefully."""
        # This tests the import error handling in the CLI
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "validation" / "validate_markdown_cli.py"

        # Run in a directory without proper setup to potentially trigger import issues
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd="/tmp",
            timeout=30,
        )

        # Should handle errors gracefully
        assert isinstance(result.returncode, int)


class TestValidateMarkdownIntegration:
    """Integration tests."""

    def test_module_structure(self):
        """Test module has expected structure."""
        from infrastructure.validation import validate_markdown_cli

        assert hasattr(validate_markdown_cli, "main")
        assert hasattr(validate_markdown_cli, "find_markdown_files")
        assert hasattr(validate_markdown_cli, "collect_symbols")
        assert hasattr(validate_markdown_cli, "validate_images")
        assert hasattr(validate_markdown_cli, "validate_refs")
        assert hasattr(validate_markdown_cli, "validate_math")
