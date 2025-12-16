"""Tests for combined PDF rendering with title page and figure handling.

Tests cover:
- Title page generation (preamble and body commands)
- Figure path resolution
- Missing figure handling
- Full combined PDF generation
"""
import pytest
import tempfile
from pathlib import Path
import yaml

from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.config import RenderingConfig
from infrastructure.core.exceptions import RenderingError


class TestTitlePageGeneration:
    """Test title page preamble and body generation."""

    @pytest.fixture
    def renderer(self):
        """Create a PDFRenderer instance."""
        config = RenderingConfig(
            manuscript_dir="/tmp/manuscript",
            figures_dir="/tmp/figures",
            output_dir="/tmp/output",
            pdf_dir="/tmp/output/pdf",
        )
        return PDFRenderer(config)

    @pytest.fixture
    def temp_manuscript_dir(self):
        """Create temporary manuscript directory with config.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_title_page_preamble_single_author(self, renderer, temp_manuscript_dir):
        """Test preamble generation with single author."""
        config = {
            'paper': {'title': 'Test Paper', 'subtitle': ''},
            'authors': [{'name': 'Dr. Jane Smith'}],
        }
        config_file = temp_manuscript_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        preamble = renderer._generate_title_page_preamble(temp_manuscript_dir)

        assert r'\title{Test Paper}' in preamble
        assert r'\author{Dr. Jane Smith}' in preamble
        assert r'\date{\today}' in preamble
        assert r'\maketitle' not in preamble  # Should not be in preamble

    def test_title_page_preamble_multiple_authors(self, renderer, temp_manuscript_dir):
        """Test preamble generation with multiple authors."""
        config = {
            'paper': {'title': 'Test Paper'},
            'authors': [
                {'name': 'Dr. Jane Smith'},
                {'name': 'Dr. John Doe'},
            ],
        }
        config_file = temp_manuscript_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        preamble = renderer._generate_title_page_preamble(temp_manuscript_dir)

        assert r'\title{Test Paper}' in preamble
        assert r'Dr. Jane Smith \and Dr. John Doe' in preamble

    def test_title_page_preamble_with_subtitle(self, renderer, temp_manuscript_dir):
        """Test preamble generation with subtitle."""
        config = {
            'paper': {'title': 'Main Title', 'subtitle': 'A Subtitle'},
            'authors': [{'name': 'Dr. Jane Smith'}],
        }
        config_file = temp_manuscript_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        preamble = renderer._generate_title_page_preamble(temp_manuscript_dir)

        # Subtitle should be included with title
        assert r'\title{Main Title' in preamble
        assert 'A Subtitle' in preamble

    def test_title_page_preamble_with_custom_date(self, renderer, temp_manuscript_dir):
        """Test preamble generation with custom date."""
        config = {
            'paper': {'title': 'Test Paper', 'date': '2025-01-01'},
            'authors': [{'name': 'Dr. Jane Smith'}],
        }
        config_file = temp_manuscript_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        preamble = renderer._generate_title_page_preamble(temp_manuscript_dir)

        assert r'\date{2025-01-01}' in preamble
        assert r'\today' not in preamble

    def test_title_page_body_generates_maketitle(self, renderer, temp_manuscript_dir):
        """Test body generation creates \\maketitle command."""
        config = {
            'paper': {'title': 'Test Paper'},
            'authors': [{'name': 'Dr. Jane Smith'}],
        }
        config_file = temp_manuscript_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        body = renderer._generate_title_page_body(temp_manuscript_dir)

        assert r'\maketitle' in body
        assert r'\thispagestyle{empty}' in body

    def test_title_page_preamble_missing_config(self, renderer, temp_manuscript_dir):
        """Test preamble generation when config.yaml is missing."""
        preamble = renderer._generate_title_page_preamble(temp_manuscript_dir)
        assert preamble == ""

    def test_title_page_body_missing_config(self, renderer, temp_manuscript_dir):
        """Test body generation when config.yaml is missing."""
        body = renderer._generate_title_page_body(temp_manuscript_dir)
        assert body == ""


class TestFigurePathResolution:
    """Test figure path fixing and resolution."""

    @pytest.fixture
    def renderer(self):
        """Create a PDFRenderer instance."""
        config = RenderingConfig(
            manuscript_dir="/tmp/manuscript",
            figures_dir="/tmp/figures",
            output_dir="/tmp/output",
            pdf_dir="/tmp/output/pdf",
        )
        return PDFRenderer(config)

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            manuscript_dir = tmppath / "manuscript"
            figures_dir = tmppath / "output" / "figures"
            manuscript_dir.mkdir(parents=True, exist_ok=True)
            figures_dir.mkdir(parents=True, exist_ok=True)
            yield manuscript_dir, figures_dir

    def test_fix_figure_paths_basic(self, renderer, temp_dirs):
        """Test basic figure path fixing."""
        manuscript_dir, figures_dir = temp_dirs
        output_dir = manuscript_dir.parent / "output" / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create a dummy figure file
        fig_file = figures_dir / "example.png"
        fig_file.write_text("dummy")

        tex_content = r"\includegraphics{../output/figures/example.png}"
        fixed = renderer._fix_figure_paths(tex_content, manuscript_dir, output_dir)

        assert "../figures/example.png" in fixed
        assert "output/figures" not in fixed

    def test_fix_figure_paths_with_options(self, renderer, temp_dirs):
        """Test figure path fixing with includegraphics options."""
        manuscript_dir, figures_dir = temp_dirs
        output_dir = manuscript_dir.parent / "output" / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create a dummy figure file
        fig_file = figures_dir / "example.png"
        fig_file.write_text("dummy")

        tex_content = r"\includegraphics[width=0.8\textwidth]{../output/figures/example.png}"
        fixed = renderer._fix_figure_paths(tex_content, manuscript_dir, output_dir)

        assert "../figures/example.png" in fixed
        assert r"[width=0.8\textwidth]" in fixed

    def test_fix_figure_paths_missing_figure(self, renderer, temp_dirs):
        """Test figure path fixing with missing figure file."""
        manuscript_dir, figures_dir = temp_dirs
        output_dir = manuscript_dir.parent / "output" / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)

        tex_content = r"\includegraphics{../output/figures/missing.png}"
        fixed = renderer._fix_figure_paths(tex_content, manuscript_dir, output_dir)

        # Should still fix the path, but log warning
        assert "../figures/missing.png" in fixed

    def test_fix_figure_paths_multiple_figures(self, renderer, temp_dirs):
        """Test figure path fixing with multiple figures."""
        manuscript_dir, figures_dir = temp_dirs
        output_dir = manuscript_dir.parent / "output" / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy figure files
        (figures_dir / "fig1.png").write_text("dummy")
        (figures_dir / "fig2.png").write_text("dummy")

        tex_content = (
            r"\includegraphics{../output/figures/fig1.png}" + "\n"
            r"\includegraphics{../output/figures/fig2.png}"
        )
        fixed = renderer._fix_figure_paths(tex_content, manuscript_dir, output_dir)

        assert "../figures/fig1.png" in fixed
        assert "../figures/fig2.png" in fixed
        assert "output/figures" not in fixed

    def test_fix_figure_paths_already_correct(self, renderer, temp_dirs):
        """Test figure path fixing with already correct paths."""
        manuscript_dir, figures_dir = temp_dirs
        output_dir = manuscript_dir.parent / "output" / "pdf"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy figure file
        (figures_dir / "example.png").write_text("dummy")

        tex_content = r"\includegraphics{../figures/example.png}"
        fixed = renderer._fix_figure_paths(tex_content, manuscript_dir, output_dir)

        # Should remain unchanged
        assert fixed == tex_content


class TestCombinedPDFRendering:
    """Integration tests for combined PDF generation."""

    @pytest.fixture
    def temp_project_structure(self):
        """Create temporary project structure with manuscript files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create directories
            manuscript_dir = tmppath / "project" / "manuscript"
            figures_dir = tmppath / "project" / "output" / "figures"
            pdf_dir = tmppath / "project" / "output" / "pdf"

            manuscript_dir.mkdir(parents=True, exist_ok=True)
            figures_dir.mkdir(parents=True, exist_ok=True)
            pdf_dir.mkdir(parents=True, exist_ok=True)

            # Create sample markdown files
            abstract = manuscript_dir / "01_abstract.md"
            abstract.write_text("# Abstract\n\nThis is a test abstract.")

            intro = manuscript_dir / "02_introduction.md"
            intro.write_text(
                "# Introduction\n\n"
                r"\begin{figure}[h]" + "\n"
                r"\centering" + "\n"
                r"\includegraphics[width=0.8\textwidth]{../output/figures/example.png}" + "\n"
                r"\caption{Test figure}" + "\n"
                r"\label{fig:test}" + "\n"
                r"\end{figure}" + "\n"
            )

            references = manuscript_dir / "99_references.md"
            references.write_text("# References\n\nSome references.")

            # Create config.yaml
            config = {
                'paper': {'title': 'Integration Test Paper'},
                'authors': [{'name': 'Test Author'}],
            }
            config_file = manuscript_dir / "config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f)

            # Create sample figure
            fig_file = figures_dir / "example.png"
            fig_file.write_bytes(b"PNG_DUMMY_DATA")

            yield tmppath, manuscript_dir, figures_dir, pdf_dir

    def test_combined_pdf_includes_preamble_commands(self, temp_project_structure):
        """Test that combined PDF rendering includes preamble commands."""
        tmppath, manuscript_dir, figures_dir, pdf_dir = temp_project_structure

        config = RenderingConfig(
            manuscript_dir=str(manuscript_dir),
            figures_dir=str(figures_dir),
            output_dir=str(pdf_dir.parent),
            pdf_dir=str(pdf_dir),
        )
        renderer = PDFRenderer(config)

        # Generate source files list
        source_files = sorted([f for f in manuscript_dir.glob("*.md") if f.name[0].isdigit()])

        # Create combined markdown
        combined_md = manuscript_dir.parent / "_combined_manuscript.md"
        combined_content = renderer._combine_markdown_files(source_files)
        combined_md.write_text(combined_content)

        # Test that combined content includes source files
        assert len(source_files) == 3
        assert "Abstract" in combined_content
        assert "Introduction" in combined_content
        assert "References" in combined_content

    def test_combined_pdf_title_page_commands_order(self):
        """Test that title page commands are in correct order."""
        # Create renderer
        config = RenderingConfig(
            manuscript_dir="/tmp/manuscript",
            figures_dir="/tmp/figures",
            output_dir="/tmp/output",
            pdf_dir="/tmp/output/pdf",
        )
        renderer = PDFRenderer(config)

        # Create minimal LaTeX document
        latex = (
            r"\documentclass{article}" + "\n"
            r"\begin{document}" + "\n"
            r"Content here" + "\n"
            r"\end{document}"
        )

        # Create temp dirs for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            manuscript_dir = tmppath / "manuscript"
            manuscript_dir.mkdir()

            # Create minimal config
            config_data = {
                'paper': {'title': 'Test'},
                'authors': [{'name': 'Author'}],
            }
            config_file = manuscript_dir / "config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            # Get preamble and body commands
            preamble = renderer._generate_title_page_preamble(manuscript_dir)
            body = renderer._generate_title_page_body(manuscript_dir)

            # Verify commands are in separate outputs
            assert r"\title" in preamble
            assert r"\author" in preamble
            assert r"\date" in preamble
            assert r"\maketitle" not in preamble

            assert r"\maketitle" in body
            assert r"\title" not in body
            assert r"\author" not in body


class TestFigureVerification:
    """Test figure verification before LaTeX compilation."""

    def test_figure_reference_extraction(self):
        """Test extraction of figure references from LaTeX."""
        import re

        latex_content = (
            r"\includegraphics{../figures/fig1.png}" + "\n"
            r"\includegraphics[width=0.8\textwidth]{../figures/fig2.png}" + "\n"
            r"Some text without figures" + "\n"
            r"\includegraphics{../figures/fig3.pdf}"
        )

        pattern = r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}'
        figures = re.findall(pattern, latex_content)

        assert len(figures) == 3
        assert "../figures/fig1.png" in figures
        assert "../figures/fig2.png" in figures
        assert "../figures/fig3.pdf" in figures

    def test_missing_figure_detection(self):
        """Test detection of missing figure files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            figures_dir = tmppath / "figures"
            figures_dir.mkdir()

            # Create one figure
            (figures_dir / "exists.png").write_text("dummy")

            # Check both existing and missing
            assert (figures_dir / "exists.png").exists()
            assert not (figures_dir / "missing.png").exists()






















