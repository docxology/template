"""Pytest configuration for infrastructure layer tests."""
import os
import pytest
from pathlib import Path
import yaml

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")


@pytest.fixture
def project_config_structure(tmp_path):
    """Create a standard project config structure for testing.

    Creates: tmp_path/projects/project/manuscript/config.yaml

    Returns:
        Tuple of (repo_root, config_file_path)
    """
    # Create project structure
    projects_dir = tmp_path / "projects"
    project_dir = projects_dir / "project"
    manuscript_dir = project_dir / "manuscript"
    manuscript_dir.mkdir(parents=True)

    config_file = manuscript_dir / "config.yaml"

    return tmp_path, config_file


@pytest.fixture
def sample_project_config():
    """Return sample project configuration data."""
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


@pytest.fixture
def project_config_file(project_config_structure, sample_project_config):
    """Create a config file with sample data.

    Returns:
        Path to the created config.yaml file
    """
    repo_root, config_file = project_config_structure

    with open(config_file, 'w') as f:
        yaml.dump(sample_project_config, f)

    return config_file


@pytest.fixture
def output_directory_structure(tmp_path):
    """Create a standard output directory structure for testing.

    Creates: tmp_path/output/ with subdirectories and sample files

    Returns:
        Path to the output directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create standard subdirectories
    subdirs = ["pdf", "web", "slides", "figures", "data", "reports", "simulations", "llm", "logs"]
    for subdir in subdirs:
        (output_dir / subdir).mkdir()

    return output_dir


@pytest.fixture
def pdf_file_fixture(tmp_path):
    """Create a sample PDF file for testing.

    Uses reportlab to create a real PDF file.

    Returns:
        Path to the created PDF file
    """
    pdf_file = tmp_path / "test.pdf"

    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(pdf_file))
        c.drawString(100, 750, "Test PDF content for validation testing")
        c.drawString(100, 730, "This is a sample PDF file created for unit tests.")
        c.drawString(100, 710, "It contains realistic content for validation purposes.")
        c.save()
    except ImportError:
        # Fallback if reportlab not available - create a fake PDF-like file
        pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n72 720 Td\n/F0 12 Tf\n(Test PDF Content) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF")

    return pdf_file


@pytest.fixture
def output_with_pdf(output_directory_structure, pdf_file_fixture):
    """Create output directory with a PDF file in the correct location.

    Returns:
        Path to the output directory with PDF in pdf/ subdirectory
    """
    output_dir = output_directory_structure

    # Copy the PDF to the correct location
    pdf_dest = output_dir / "pdf" / "project_combined.pdf"
    pdf_dest.write_bytes(pdf_file_fixture.read_bytes())

    return output_dir

@pytest.fixture(scope="session")
def ensure_ollama_for_tests():
    """Ensure Ollama is running and functional for tests.

    This fixture:
    - Checks if Ollama is running
    - Attempts to start Ollama automatically if not running
    - Verifies Ollama is responding and has models
    - FAILS loudly if Ollama can't be started or isn't working

    This fixture runs once per test session and ensures all tests
    marked with @pytest.mark.requires_ollama have a working Ollama instance.
    """
    from infrastructure.llm.utils.ollama import (
        is_ollama_running,
        ensure_ollama_ready,
        get_model_names,
    )
    from infrastructure.core.logging_utils import get_logger

    logger = get_logger(__name__)

    # Check if Ollama is already running
    if is_ollama_running():
        logger.info("✓ Ollama server is already running")
    else:
        logger.warning("⚠️  Ollama server is not running - attempting to start...")
        if not ensure_ollama_ready(auto_start=True):
            pytest.fail(
                "\n" + "="*80 + "\n"
                "❌ CRITICAL: Ollama server cannot be started for tests!\n"
                "="*80 + "\n"
                "Tests require a working Ollama installation.\n\n"
                "Troubleshooting:\n"
                "  1. Install Ollama: https://ollama.ai\n"
                "  2. Start Ollama manually: ollama serve\n"
                "  3. Verify installation: ollama --version\n"
                "  4. Check if port 11434 is available: lsof -i :11434\n"
                "  5. Install at least one model: ollama pull llama3-gradient\n\n"
                "To skip Ollama tests: pytest -m 'not requires_ollama'\n"
                "="*80
            )

    # Verify Ollama has models available
    models = get_model_names()
    if not models:
        pytest.fail(
            "\n" + "="*80 + "\n"
            "❌ CRITICAL: Ollama server is running but has no models!\n"
            "="*80 + "\n"
            "Tests require at least one Ollama model to be installed.\n\n"
            "Install a model:\n"
            "  ollama pull llama3-gradient    # Recommended (4.7GB, 256K context)\n"
            "  ollama pull llama3.1:latest     # Alternative (4.7GB, 128K context)\n"
            "  ollama pull gemma2:2b          # Small/fast option (2B params)\n\n"
            "Verify models: ollama list\n"
            "="*80
        )

    logger.info(f"✓ Ollama ready for tests with {len(models)} model(s): {', '.join(models[:3])}")
    return True
