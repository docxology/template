"""Markdown validation: image, reference, math, and whole-document checks."""

import os
import sys
import pytest
from infrastructure.validation.content.markdown_validator import (
    validate_images,
    validate_markdown,
    validate_math,
    validate_refs,
)

# Add infrastructure to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)


class TestValidateImages:
    """Test validate_images function."""

    def test_detects_missing_image(self, tmp_path):
        """Test validate_images detects missing images."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("![alt text](../output/figures/missing.png)")

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Missing referenced image: '../output/figures/missing.png'" in problems[0].message

    def test_validates_existing_image(self, tmp_path):
        """Test validate_images doesn't flag existing images."""
        # Create test markdown file and image
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("![alt text](../output/figures/existing.png)")
        (tmp_path / "output" / "figures").mkdir(parents=True)
        (tmp_path / "output" / "figures" / "existing.png").write_text("fake image")

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 0

    def test_ignores_image_syntax_inside_fenced_code(self, tmp_path):
        """Example figure markdown in fenced blocks must not trigger IMG_MISSING."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "```markdown\n![Caption](../output/figures/example.png)\n```\n",
            encoding="utf-8",
        )

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert problems == []

    def test_absolute_path(self, tmp_path):
        """Test validate_images with absolute image paths."""
        # Create test markdown file with absolute path
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        abs_image_path = str(tmp_path / "absolute_image.png")
        (manuscript / "test.md").write_text(f"![alt text]({abs_image_path})")

        # Don't create the image file so it will be missing
        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Missing referenced image" in problems[0].message

    def test_relative_path_not_absolute_after_normpath(self, tmp_path, monkeypatch):
        """Test validate_images with relative path that stays relative after normpath.

        This covers line 94 where abs_path is joined with repo_root when not absolute.
        """
        # Create a manuscript directory with an image reference
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir(parents=True)

        (manuscript / "test.md").write_text("![alt text](../output/figures/test.png)")

        # Change to tmp_path so we can use relative paths
        monkeypatch.chdir(tmp_path)

        # Pass RELATIVE path to markdown file - this triggers line 94
        # because dirname("manuscript/test.md") = "manuscript"
        # and join("manuscript", "../output/figures/test.png") = "output/figures/test.png" (relative!)
        relative_md_path = "manuscript/test.md"

        problems = validate_images([relative_md_path], tmp_path)

        # Should report missing image since we didn't create it
        assert len(problems) == 1
        assert "Missing referenced image" in problems[0].message

    def test_relative_path_exists_after_repo_root_join(self, tmp_path):
        """Test validate_images with relative path that exists when joined with repo_root.

        This covers line 94 with a file that actually exists.
        """
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()

        # Create the image in a relative location from manuscript
        figures_dir = manuscript / "figures"
        figures_dir.mkdir()
        (figures_dir / "local_image.png").write_text("fake image")

        # Reference with simple relative path
        (manuscript / "test.md").write_text("![alt text](figures/local_image.png)")

        problems = validate_images([str(manuscript / "test.md")], tmp_path)

        # Image exists, should have no problems
        assert len(problems) == 0


class TestValidateRefs:
    """Test validate_refs function."""

    def test_detects_missing_equation_label(self, tmp_path):
        """Test validate_refs detects missing equation labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Reference to \\eqref{eq:missing}")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert len(problems) == 1
        assert "Missing equation label for \\eqref{eq:missing}" in problems[0].message

    def test_detects_missing_anchor(self, tmp_path):
        """Test validate_refs detects missing anchors."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Link to [section](#missing_anchor)")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert len(problems) == 1
        assert "Missing anchor/label for internal link (#missing_anchor)" in problems[0].message

    def test_ignores_markdown_link_pattern_inside_fenced_code(self, tmp_path):
        """LaTeX like p(#1) in ``` blocks must not be reported as (#1) internal links."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("```latex\n" r"\newcommand{\gen}[1]{p(#1)}" "\n```\n")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert not any("(#1)" in p.message for p in problems)

    def test_detects_bare_url(self, tmp_path):
        """Test validate_refs detects bare URLs."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Visit https://example.com for more info")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        assert len(problems) == 1
        assert "Bare URL found" in problems[0].message

    def test_detects_non_informative_link(self, tmp_path):
        """Test validate_refs detects non-informative link text."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("[https://example.com](https://example.com)")

        problems = validate_refs([str(manuscript / "test.md")], tmp_path, set(), set())

        # The regex patterns can detect multiple issues with the same text
        assert len(problems) >= 1
        assert any("Non-informative link text" in p.message for p in problems)


class TestValidateMath:
    """Test validate_math function."""

    def test_detects_inline_dollar_display_math(self, tmp_path):
        """Test validate_math detects inline dollar-display notation."""
        # Create test markdown file with inline $$ math
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Math: $$x^2 + y^2 = z^2$$")

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "inline or unbalanced $$" in problems[0].message

    def test_allows_isolated_dollar_display_math_blocks(self, tmp_path):
        """Pandoc-native display math blocks are valid for PDF and HTML."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "$$x^2 + y^2 = z^2$$\n\n$$\na+b=c\n$$\n",
            encoding="utf-8",
        )

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert problems == []

    def test_detects_bracket_math(self, tmp_path):
        """Test validate_math detects bracket math notation."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("Math: \\[x^2 + y^2 = z^2\\]")

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Use equation environment instead of \\[ \\]" in problems[0].message

    def test_detects_missing_label(self, tmp_path):
        """Test validate_math detects equations without labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(r"\begin{equation}x^2 + y^2 = z^2\end{equation}")

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Equation missing \\label{...}" in problems[0].message

    def test_detects_duplicate_label(self, tmp_path):
        """Test validate_math detects duplicate equation labels."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            r"\begin{equation}\label{eq:duplicate}x^2\end{equation}" + "\n"
            r"\begin{equation}\label{eq:duplicate}y^2\end{equation}"
        )

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 1
        assert "Duplicate equation label '{eq:duplicate}'" in problems[0].message

    def test_accepts_valid_equations(self, tmp_path):
        """Test validate_math accepts valid labeled equations."""
        # Create test markdown file
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text(
            "\\begin{equation}\\label{eq:valid1}x^2 + y^2 = z^2\\end{equation}\n"
            "\\begin{equation}\\label{eq:valid2}a^2 + b^2 = c^2\\end{equation}"
        )

        problems = validate_math([str(manuscript / "test.md")], tmp_path)

        assert len(problems) == 0


class TestValidateMarkdown:
    """Test validate_markdown function."""

    def test_no_problems_returns_zero(self, tmp_path):
        """Test validate_markdown returns 0 when no problems found."""
        # Create test markdown directory with valid content
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("# Test\n\nNo problems here.")

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)

        assert exit_code == 0
        assert problems == []

    def test_problems_non_strict_returns_zero(self, tmp_path):
        """Test validate_markdown returns 0 with problems in non-strict mode."""
        # Create test markdown directory with problems
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("\\begin{equation}x^2\\end{equation}")

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)

        assert exit_code == 0
        assert len(problems) > 0

    def test_problems_strict_returns_one(self, tmp_path):
        """Test validate_markdown returns 1 with problems in strict mode."""
        # Create test markdown directory with an ERROR-level problem
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "test.md").write_text("![Missing image](../output/figures/missing.png)")

        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)

        assert exit_code == 1
        assert len(problems) > 0

    def test_nonexistent_directory_raises(self, tmp_path):
        """Test validate_markdown raises on nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            validate_markdown(tmp_path / "nonexistent", tmp_path)

    def test_empty_directory_returns_zero(self, tmp_path):
        """Test validate_markdown with empty directory."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()

        problems, exit_code = validate_markdown(manuscript, tmp_path)

        assert exit_code == 0
        assert problems == []
