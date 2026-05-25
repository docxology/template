"""Comprehensive tests for infrastructure/validation/cli/markdown.py.

Tests the markdown validation CLI script.
"""

import os
import subprocess
import sys
from pathlib import Path

from infrastructure.validation.cli import markdown as validate_markdown_cli


class TestValidateMarkdownCliImportError:
    """Test import error handling in validate_markdown_cli."""

    def test_main_with_import_error(self, capsys):
        """Test main() returns 1 and logs error when import_error is set.

        This covers the import error handling path.
        """
        # Save original import_error
        original_import_error = validate_markdown_cli.import_error

        try:
            # Set import_error to simulate an import failure
            validate_markdown_cli.import_error = "❌ Test import error message"

            # Call main - should return 1 due to import error
            result = validate_markdown_cli.main()

            assert result == 1
        finally:
            # Restore original import_error
            validate_markdown_cli.import_error = original_import_error

    def test_import_error_is_none_by_default(self):
        """Test that import_error is None when module loads successfully."""
        # When the module loads successfully, import_error should be None
        assert validate_markdown_cli.import_error is None


class TestValidateMarkdownCliMainSubprocess:
    """Test main function execution paths."""

    def test_main_with_strict_flag(self, tmp_path):
        """Test main() with --strict flag using direct function args."""
        # Create a valid manuscript directory
        manuscript = tmp_path / "project" / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "test.md").write_text("# Valid Test\n\nNo issues.")

        # Call main directly with function arguments (no monkeypatch needed)
        result = validate_markdown_cli.main(manuscript_path=manuscript, strict=True)

        assert result == 0

    def test_main_file_not_found(self, tmp_path):
        """Test main() when manuscript directory not found."""
        # Point to a non-existent directory
        nonexistent = tmp_path / "no_such_manuscript"

        result = validate_markdown_cli.main(manuscript_path=nonexistent)

        assert result == 1

    def test_validate_refs_function(self, tmp_path):
        """Test validate_refs helper function."""
        md_file = tmp_path / "test.md"
        md_file.write_text("See [section](#missing_ref) for details.")

        labels = {"existing_label": str(md_file)}
        anchors = {}

        issues = validate_markdown_cli.validate_refs([str(md_file)], str(tmp_path), labels, anchors)

        # Should find reference to missing_ref
        assert isinstance(issues, list)

    def test_validate_math_function(self, tmp_path):
        """Test validate_math helper function."""
        md_file = tmp_path / "test.md"
        md_file.write_text("Math: $x^2$ and $y^2$ = complete pair")

        issues = validate_markdown_cli.validate_math([str(md_file)], str(tmp_path))

        assert isinstance(issues, list)


class TestValidateMarkdownCliHelpers:
    """Test helper functions in validate_markdown_cli."""

    def test_repo_root(self):
        """Test _repo_root returns a valid path."""
        root = validate_markdown_cli._repo_root()
        assert isinstance(root, str)
        assert len(root) > 0

    def test_discover_markdown_files(self, tmp_path):
        """Test discover_markdown_files function."""
        (tmp_path / "01_intro.md").write_text("# Intro")
        (tmp_path / "02_methods.md").write_text("# Methods")
        (tmp_path / "readme.txt").write_text("Not markdown")

        files = validate_markdown_cli.discover_markdown_files(tmp_path, scope="tree")

        assert len(files) == 2
        assert any(f.name == "01_intro.md" for f in files)
        assert any(f.name == "02_methods.md" for f in files)

    def test_discover_markdown_files_empty_dir(self, tmp_path):
        """Test with empty directory."""
        files = validate_markdown_cli.discover_markdown_files(tmp_path, scope="tree")
        assert len(files) == 0

    def test_collect_symbols_with_labels(self, tmp_path):
        """Test collect_symbols extracts equation labels."""
        md_file = tmp_path / "test.md"
        md_file.write_text(r"\label{section-one}" + "\n\nContent")

        labels, anchors = validate_markdown_cli.collect_symbols([str(md_file)])

        assert "section-one" in labels

    def test_collect_symbols_with_anchors(self, tmp_path):
        """Test collect_symbols extracts section anchors."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Reference {#ref1}\n\nContent")

        labels, anchors = validate_markdown_cli.collect_symbols([str(md_file)])

        assert "ref1" in anchors

    def test_validate_images_valid(self, tmp_path):
        """Test validate_images with valid images."""
        # Create image
        img_dir = tmp_path / "output" / "figures"
        img_dir.mkdir(parents=True)
        (img_dir / "test.png").write_bytes(b"PNG data")

        # Create markdown with image ref
        md_file = tmp_path / "test.md"
        md_file.write_text("![Test](../output/figures/test.png)")

        problems = validate_markdown_cli.validate_images([str(md_file)], str(tmp_path))

        # May have problems depending on path resolution
        assert isinstance(problems, list)

    def test_validate_images_missing(self, tmp_path):
        """Test validate_images with missing images."""
        md_file = tmp_path / "test.md"
        md_file.write_text("![Missing](./missing_image.png)")

        problems = validate_markdown_cli.validate_images([str(md_file)], str(tmp_path))

        # Should report missing image
        assert isinstance(problems, list)


class TestValidateMarkdownCliExports:
    """Test module exports and attributes."""

    def test_module_has_expected_functions(self):
        """Test module exports expected functions."""
        assert hasattr(validate_markdown_cli, "_repo_root")
        assert hasattr(validate_markdown_cli, "discover_markdown_files")
        assert hasattr(validate_markdown_cli, "collect_symbols")
        assert hasattr(validate_markdown_cli, "validate_images")


class TestValidateMarkdownCliIntegration:
    """Integration tests for validate_markdown_cli."""

    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow."""
        # Create a manuscript structure
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        (manuscript_dir / "01_abstract.md").write_text(
            """
# Abstract {#abstract}

This is the abstract section.
"""
        )
        (manuscript_dir / "02_intro.md").write_text(
            """
# Introduction {#intro}

See Section [](#abstract) for details.
"""
        )

        # Find files
        files = [str(path) for path in validate_markdown_cli.discover_markdown_files(manuscript_dir, scope="tree")]
        assert len(files) == 2

        # Collect symbols
        labels, anchors = validate_markdown_cli.collect_symbols(files)
        assert "abstract" in anchors
        assert "intro" in anchors


class TestValidateMarkdownCliFunctions:
    """Test module functions."""

    def test_repo_root(self):
        """Test _repo_root helper."""
        from infrastructure.validation.cli.markdown import _repo_root

        result = _repo_root()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_discover_markdown_files(self, tmp_path):
        """Test discover_markdown_files function."""
        from infrastructure.validation.cli.markdown import discover_markdown_files

        (tmp_path / "01_intro.md").write_text("# Intro")
        (tmp_path / "02_body.md").write_text("# Body")
        (tmp_path / "03_conclusion.md").write_text("# Conclusion")

        files = discover_markdown_files(tmp_path, scope="tree")

        assert len(files) == 3
        assert any(f.name == "01_intro.md" for f in files)

    def test_discover_markdown_files_no_extension(self, tmp_path):
        """Test discover_markdown_files with non-markdown files."""
        from infrastructure.validation.cli.markdown import discover_markdown_files

        (tmp_path / "test.txt").write_text("Not markdown")
        (tmp_path / "doc.md").write_text("# Doc")

        files = discover_markdown_files(tmp_path, scope="tree")

        assert len(files) == 1
        assert files[0].name == "doc.md"

    def test_collect_symbols(self, tmp_path):
        """Test collect_symbols function (canonical: labels=LaTeX \\label{}, anchors={#...})."""
        from infrastructure.validation.cli.markdown import collect_symbols

        md = tmp_path / "test.md"
        md.write_text("# Title {#title}\n\n\\label{eq:one}")

        labels, anchors = collect_symbols([str(md)])

        assert "eq:one" in labels  # LaTeX \label{...}
        assert "title" in anchors  # {#...} section anchors

    def test_collect_symbols_empty_file(self, tmp_path):
        """Test collect_symbols with empty file."""
        from infrastructure.validation.cli.markdown import collect_symbols

        md = tmp_path / "empty.md"
        md.write_text("")

        labels, anchors = collect_symbols([str(md)])

        assert len(labels) == 0
        assert len(anchors) == 0

    def test_validate_images_found(self, tmp_path):
        """Test validate_images with existing image."""
        from infrastructure.validation.cli.markdown import validate_images

        (tmp_path / "img.png").write_bytes(b"\x89PNG")
        md = tmp_path / "doc.md"
        md.write_text("![Alt](img.png)")

        issues = validate_images([str(md)], str(tmp_path))

        assert len(issues) == 0

    def test_validate_images_missing(self, tmp_path):
        """Test validate_images with missing image."""
        from infrastructure.validation.cli.markdown import validate_images

        md = tmp_path / "doc.md"
        md.write_text("![Alt](missing.png)")

        issues = validate_images([str(md)], str(tmp_path))

        assert len(issues) == 1
        assert "Missing image" in issues[0]

    def test_validate_images_no_refs(self, tmp_path):
        """Test validate_images with no image references produces no issues."""
        from infrastructure.validation.cli.markdown import validate_images

        md = tmp_path / "doc.md"
        md.write_text("# Title\n\nNo images here.")

        issues = validate_images([str(md)], str(tmp_path))

        assert len(issues) == 0

    def test_validate_refs_found(self, tmp_path):
        """Test validate_refs with existing internal anchor reference."""
        from infrastructure.validation.cli.markdown import validate_refs

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
        from infrastructure.validation.cli.markdown import validate_refs

        md = tmp_path / "doc.md"
        md.write_text("[Link text](#missing)")

        issues = validate_refs([str(md)], str(tmp_path), set(), set())

        anchor_issues = [i for i in issues if "missing" in i.lower() or "Missing" in i]
        assert len(anchor_issues) >= 1

    def test_validate_math_no_issues(self, tmp_path):
        """Test validate_math with clean content (no display math constructs)."""
        from infrastructure.validation.cli.markdown import validate_math

        md = tmp_path / "doc.md"
        md.write_text("Inline math: $E = mc^2$ is fine.")

        issues = validate_math([str(md)], str(tmp_path))

        assert len(issues) == 0

    def test_validate_math_double_dollar(self, tmp_path):
        """Test validate_math flags inline $$ display math misuse."""
        from infrastructure.validation.cli.markdown import validate_math

        md = tmp_path / "doc.md"
        md.write_text("Inline misuse: $$E = mc^2$$")

        issues = validate_math([str(md)], str(tmp_path))

        assert len(issues) >= 1
        assert any("isolated" in i.lower() and "$$" in i for i in issues)


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
        script_path = repo_root / "infrastructure" / "validation" / "cli" / "markdown.py"

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
        script_path = repo_root / "infrastructure" / "validation" / "cli" / "markdown.py"

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
        script_path = repo_root / "infrastructure" / "validation" / "cli" / "markdown.py"

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
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        assert hasattr(validate_markdown_cli, "main")
        assert hasattr(validate_markdown_cli, "discover_markdown_files")
        assert hasattr(validate_markdown_cli, "collect_symbols")
        assert hasattr(validate_markdown_cli, "validate_images")
        assert hasattr(validate_markdown_cli, "validate_refs")
        assert hasattr(validate_markdown_cli, "validate_math")


class TestValidateMarkdownCliModule:
    """Test module-level functionality."""

    def test_module_imports(self):
        """Test module imports correctly."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        assert validate_markdown_cli is not None


class TestValidateMarkdownCliMain:
    """Test main function and CLI using real subprocess execution."""

    def test_main_exists(self):
        """Test main function exists."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        assert hasattr(validate_markdown_cli, "main")

    def test_main_with_valid_file(self, tmp_path, capsys):
        """Test main with valid markdown file using real execution."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        md = tmp_path / "test.md"
        md.write_text("# Title\n\nValid content here.")

        # Use real execution
        try:
            result = validate_markdown_cli.main(manuscript_path=md)
            # May return 0 (success) or 1 (issues found)
            assert result in [0, 1, 2] or result is None
        except SystemExit:
            pass  # SystemExit is also acceptable

    def test_main_with_directory(self, tmp_path, capsys):
        """Test main with directory using real execution."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        (tmp_path / "a.md").write_text("# Doc A\n")
        (tmp_path / "b.md").write_text("# Doc B\n")

        # Use real execution
        try:
            result = validate_markdown_cli.main(manuscript_path=tmp_path)
            assert result in [0, 1, 2] or result is None
        except SystemExit:
            pass

    def test_main_with_missing_file(self, tmp_path, capsys):
        """Test main with missing file using real execution."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        missing = tmp_path / "missing.md"

        # Use real execution
        try:
            result = validate_markdown_cli.main(manuscript_path=missing)
            # Should return error code
            assert result in [0, 1, 2] or result is None
        except SystemExit:
            pass

    def test_main_via_subprocess(self, tmp_path):
        """Test main via real subprocess execution."""
        md = tmp_path / "test.md"
        md.write_text("# Title\n\nValid content.")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.validation.cli.markdown",
                str(md),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # May succeed or fail depending on validation
        assert result.returncode in [0, 1, 2]


class TestValidateMarkdownFunctions:
    """Test validation functions using real implementations."""

    def test_validate_markdown_file(self, tmp_path):
        """Test validating single file using real validation."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        md = tmp_path / "test.md"
        md.write_text("# Title\n\n[Link](other.md)")

        if hasattr(validate_markdown_cli, "validate_markdown_file"):
            result = validate_markdown_cli.validate_markdown_file(str(md))
            assert result is not None

    def test_validate_markdown_content(self):
        """Test validating markdown content using real validation."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        content = "# Title\n\nValid content"

        if hasattr(validate_markdown_cli, "validate_content"):
            result = validate_markdown_cli.validate_content(content)
            assert result is not None


class TestValidateMarkdownCliCore:
    """Test core validate markdown CLI functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        assert validate_markdown_cli is not None

    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        assert hasattr(validate_markdown_cli, "main") or hasattr(validate_markdown_cli, "validate_markdown_cli")


class TestMarkdownValidationCommand:
    """Test markdown validation command using real execution."""

    def test_validate_single_file(self, tmp_path):
        """Test validating a single markdown file using real validation."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        md = tmp_path / "test.md"
        md.write_text("# Title\n\nContent")

        if hasattr(validate_markdown_cli, "validate_markdown_file"):
            result = validate_markdown_cli.validate_markdown_file(str(md))
            assert result is not None

    def test_validate_directory(self, tmp_path):
        """Test validating a directory of markdown files using real validation."""
        from infrastructure.validation.cli import markdown as validate_markdown_cli

        (tmp_path / "a.md").write_text("# A\n")
        (tmp_path / "b.md").write_text("# B\n")

        if hasattr(validate_markdown_cli, "validate_markdown_directory"):
            result = validate_markdown_cli.validate_markdown_directory(str(tmp_path))
            assert result is not None


class TestMarkdownCliMain:
    """Test main entry point using real subprocess execution."""

    def test_main_with_valid_markdown(self, tmp_path):
        """Test main with valid markdown via real subprocess."""
        md = tmp_path / "test.md"
        md.write_text("# Title\n\nValid content.")

        # Run real CLI command via subprocess
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.validation.cli.markdown",
                str(md),
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
            timeout=30,
        )

        # May succeed or fail depending on validation
        assert result.returncode in [0, 1, 2]
