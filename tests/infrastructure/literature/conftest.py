import pytest
from pathlib import Path
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.sources import SearchResult

@pytest.fixture
def mock_config(tmp_path):
    """Create test configuration with temporary directories."""
    config = LiteratureConfig()
    config.download_dir = str(tmp_path / "pdfs")
    config.bibtex_file = str(tmp_path / "refs.bib")
    config.library_index_file = str(tmp_path / "library.json")
    config.arxiv_delay = 0.0  # Speed up tests
    config.semanticscholar_delay = 0.0  # Speed up tests
    config.retry_delay = 0.0  # Speed up tests
    config.retry_attempts = 1  # Speed up tests
    return config

@pytest.fixture
def sample_result():
    """Create a sample SearchResult for testing."""
    return SearchResult(
        title="Test Paper",
        authors=["Author One", "Author Two"],
        year=2023,
        abstract="This is a test abstract.",
        url="http://example.com/paper",
        doi="10.1234/test.123",
        source="test",
        pdf_url="http://example.com/paper.pdf",
        venue="Journal of Testing"
    )
