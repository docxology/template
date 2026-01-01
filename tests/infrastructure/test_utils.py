"""Test utilities for infrastructure layer tests.

This module provides helper functions for creating test data, fixtures,
and common test setup patterns. All functions follow the "no mocks" policy
and create real data for testing.
"""
from pathlib import Path
from typing import Dict, Any
import yaml


def create_project_config_structure(repo_root: Path, project_name: str = "project") -> Path:
    """Create a standard project config structure.

    Args:
        repo_root: Repository root directory
        project_name: Name of the project

    Returns:
        Path to the created config.yaml file
    """
    config_dir = repo_root / "projects" / project_name / "manuscript"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.yaml"
    return config_file


def create_sample_config_data() -> Dict[str, Any]:
    """Create sample configuration data for testing.

    Returns:
        Dictionary with sample config data
    """
    return {
        'paper': {
            'title': 'Test Research Paper',
            'subtitle': 'A comprehensive study',
            'version': '1.0'
        },
        'authors': [
            {
                'name': 'Dr. Test Author',
                'orcid': '0000-0000-0000-1234',
                'email': 'test@example.com',
                'corresponding': True
            }
        ],
        'publication': {
            'doi': '10.5281/zenodo.12345678'
        },
        'llm': {
            'translations': {
                'enabled': True,
                'languages': ['zh', 'hi', 'ru']
            }
        }
    }


def write_config_file(config_file: Path, config_data: Dict[str, Any]) -> None:
    """Write configuration data to a YAML file.

    Args:
        config_file: Path to config file to create
        config_data: Configuration data to write
    """
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)


def create_output_directory_structure(output_dir: Path) -> None:
    """Create standard output directory structure.

    Args:
        output_dir: Output directory to create structure in
    """
    # Create standard subdirectories
    subdirs = ["pdf", "web", "slides", "figures", "data", "reports", "simulations", "llm", "logs"]
    for subdir in subdirs:
        (output_dir / subdir).mkdir(exist_ok=True)


def create_pdf_file(pdf_path: Path, content: str = "Test PDF content", size_kb: int = 100) -> None:
    """Create a PDF file for testing.

    Uses reportlab if available, otherwise creates a minimal PDF-like file.

    Args:
        pdf_path: Path where to create the PDF file
        content: Text content to include in the PDF
        size_kb: Approximate size of the PDF file in KB
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        # Add multiple pages to reach desired size
        lines_per_page = 50
        lines = content.split('\n') if '\n' in content else [content] * (size_kb * 10)

        for i in range(0, len(lines), lines_per_page):
            page_lines = lines[i:i + lines_per_page]
            c.drawString(72, 750, f"Page {i // lines_per_page + 1}")
            y = 720
            for line in page_lines:
                if y > 72:  # Don't go below bottom margin
                    c.drawString(72, y, line[:80])  # Limit line length
                    y -= 14
            c.showPage()

        c.save()

    except ImportError:
        # Fallback: create a minimal PDF-like file
        pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length {len(content.encode())}
/Filter /FlateDecode
>>
stream
{content}
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000200 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{284 + len(content)}
%%EOF"""

        pdf_path.write_text(pdf_content)


def create_output_with_pdf(output_dir: Path, pdf_name: str = "project_combined.pdf") -> Path:
    """Create output directory with a PDF file in the pdf/ subdirectory.

    Args:
        output_dir: Output directory to create structure in
        pdf_name: Name of the PDF file to create

    Returns:
        Path to the created PDF file
    """
    create_output_directory_structure(output_dir)

    pdf_file = output_dir / "pdf" / pdf_name
    create_pdf_file(pdf_file)

    return pdf_file


def create_test_manuscript_files(manuscript_dir: Path) -> Dict[str, Path]:
    """Create sample manuscript files for testing.

    Args:
        manuscript_dir: Directory to create manuscript files in

    Returns:
        Dictionary mapping file types to created file paths
    """
    manuscript_dir.mkdir(parents=True, exist_ok=True)

    files = {}

    # Create markdown files
    sections = [
        ("01_abstract", "# Abstract\n\nThis is a test abstract."),
        ("02_introduction", "# Introduction\n\nThis is a test introduction."),
        ("03_methodology", "# Methodology\n\nThis is a test methodology."),
    ]

    for filename, content in sections:
        file_path = manuscript_dir / f"{filename}.md"
        file_path.write_text(content)
        files[filename] = file_path

    return files


def create_test_figure_files(figures_dir: Path) -> Dict[str, Path]:
    """Create sample figure files for testing.

    Args:
        figures_dir: Directory to create figure files in

    Returns:
        Dictionary mapping figure names to created file paths
    """
    figures_dir.mkdir(parents=True, exist_ok=True)

    files = {}

    # Create PNG-like files (minimal valid PNG header)
    png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # Minimal PNG-like content

    figures = ["figure1.png", "figure2.png", "plot.png"]
    for fig_name in figures:
        fig_path = figures_dir / fig_name
        fig_path.write_bytes(png_header)
        files[fig_name] = fig_path

    return files


def cleanup_test_directory(test_dir: Path) -> None:
    """Clean up test directory and its contents.

    Args:
        test_dir: Directory to clean up
    """
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)