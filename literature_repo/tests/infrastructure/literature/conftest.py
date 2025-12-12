import pytest
import json
from pathlib import Path
from infrastructure.literature.core import LiteratureConfig
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.library.index import LibraryEntry

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

@pytest.fixture
def ensure_ollama_available():
    """Ensure Ollama is available, skip test if not.
    
    Returns:
        LLMClient instance if Ollama is available.
    """
    from infrastructure.llm import LLMClient, is_ollama_running
    
    if not is_ollama_running():
        pytest.skip("Ollama not running - start with 'ollama serve'")
    
    client = LLMClient()
    if not client.check_connection():
        pytest.skip("Ollama connection failed")
    
    return client

@pytest.fixture
def real_library_entries(tmp_path):
    """Create real library entries for testing."""
    entries = [
        LibraryEntry(
            citation_key="friston2016active",
            title="Active Inference: A Process Theory",
            authors=["Karl Friston", "Thomas H. B. FitzGerald"],
            year=2016,
            doi="10.1162/neco_a_00912",
            source="openalex",
            url="https://openalex.org/W2552810632",
            abstract="This article describes a process theory based on active inference.",
            venue="Neural Computation",
            citation_count=1093,
        ),
        LibraryEntry(
            citation_key="test2020machine",
            title="Machine Learning in Physics",
            authors=["Author A", "Author B"],
            year=2020,
            doi="10.1234/test1",
            source="arxiv",
            url="https://example.com/1",
            abstract="This paper discusses machine learning applications in physics research.",
            venue="Journal of Physics",
            citation_count=50,
        ),
        LibraryEntry(
            citation_key="test2021deep",
            title="Deep Learning for Biology",
            authors=["Author C", "Author D"],
            year=2021,
            doi="10.1234/test2",
            source="semanticscholar",
            url="https://example.com/2",
            abstract="Deep learning methods for biological data analysis.",
            venue="Nature Biology",
            citation_count=100,
        ),
        LibraryEntry(
            citation_key="test2022neural",
            title="Neural Networks and Active Inference",
            authors=["Author A", "Author E"],
            year=2022,
            doi="10.1234/test3",
            source="arxiv",
            url="https://example.com/3",
            abstract="Neural networks and active inference in cognitive science.",
            venue="Cognitive Science",
            citation_count=75,
        ),
    ]
    
    # Create library.json file
    library_file = tmp_path / "library.json"
    library_data = {
        "version": "1.0",
        "updated": "2024-01-01T00:00:00",
        "count": len(entries),
        "entries": {entry.citation_key: entry.to_dict() for entry in entries},
    }
    library_file.write_text(json.dumps(library_data))
    
    return entries

@pytest.fixture
def real_pdf_file(tmp_path):
    """Create a real PDF file for testing."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_path = tmp_path / "test_paper.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        # Add title
        c.drawString(100, 750, "Test Paper: Machine Learning in Physics")
        
        # Add abstract
        c.drawString(100, 730, "Abstract")
        c.drawString(100, 710, "This is a comprehensive scientific paper about machine learning")
        c.drawString(100, 690, "applications in physics research. The paper presents novel methods")
        c.drawString(100, 670, "for data analysis and optimization using neural networks.")
        
        # Add introduction
        c.drawString(100, 630, "Introduction")
        c.drawString(100, 610, "Machine learning has become increasingly important in physics.")
        c.drawString(100, 590, "This paper explores various applications and methodologies.")
        
        # Add methods
        c.drawString(100, 550, "Methods")
        c.drawString(100, 530, "We used neural networks to analyze physical systems.")
        c.drawString(100, 510, "The architecture consists of multiple layers with activation functions.")
        
        # Add results
        c.drawString(100, 470, "Results")
        c.drawString(100, 450, "Our results show significant improvements over baseline methods.")
        c.drawString(100, 430, "The neural network achieved 95% accuracy on test data.")
        
        # Add discussion
        c.drawString(100, 390, "Discussion")
        c.drawString(100, 370, "These findings have important implications for physics research.")
        c.drawString(100, 350, "The methods can be applied to various physical systems.")
        
        # Add conclusion
        c.drawString(100, 310, "Conclusion")
        c.drawString(100, 290, "Machine learning is valuable for physics research.")
        c.drawString(100, 270, "Future work will explore additional applications.")
        
        # Add references
        c.drawString(100, 230, "References")
        c.drawString(100, 210, "[1] Author et al. (2020) Machine Learning Methods. Journal of Physics.")
        c.drawString(100, 190, "[2] Researcher et al. (2021) Neural Networks in Science. Nature.")
        
        c.save()
        return pdf_path
    except ImportError:
        # Fallback: create minimal PDF
        pdf_path = tmp_path / "test_paper.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
        return pdf_path

@pytest.fixture
def real_extracted_texts(tmp_path, real_library_entries):
    """Create real extracted text files for testing."""
    extracted_dir = tmp_path / "extracted_text"
    extracted_dir.mkdir(exist_ok=True)
    
    texts = {
        "friston2016active": """Active Inference: A Process Theory

Abstract
This article describes a process theory based on active inference and belief propagation. Starting from the premise that all neuronal processing can be explained by maximizing Bayesian model evidence, we ask whether neuronal responses can be described as a gradient descent on variational free energy.

Introduction
Active inference provides a formal explanation for reward seeking, context learning, and epistemic foraging. The theory has applications across neuroscience and cognitive science.

Methods
We derive the neuronal dynamics implicit in this description and reproduce a remarkable range of well-characterized neuronal phenomena.

Results
These include repetition suppression, mismatch negativity, violation responses, place-cell activity, phase precession, theta sequences, theta-gamma coupling, evidence accumulation, race-to-bound dynamics, and transfer of dopamine responses.

Conclusion
The approximately Bayes' optimal behavior prescribed by these dynamics has a degree of face validity, providing a formal explanation for various cognitive phenomena.""",
        "test2020machine": """Machine Learning in Physics

Abstract
This paper discusses machine learning applications in physics research. We present novel methods for analyzing physical systems using neural networks.

Introduction
Machine learning has become increasingly important in physics. Traditional methods often struggle with complex systems.

Methods
We used neural networks with multiple layers to analyze physical data. The architecture includes convolutional and fully connected layers.

Results
Our results show significant improvements over baseline methods. The neural network achieved high accuracy on test datasets.

Conclusion
Machine learning is valuable for physics research and can be applied to various physical systems.""",
    }
    
    for citation_key, text in texts.items():
        text_file = extracted_dir / f"{citation_key}.txt"
        text_file.write_text(text)
    
    return extracted_dir
