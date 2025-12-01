"""Configuration management for the literature search module."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LiteratureConfig:
    """Configuration for literature search.
    
    Attributes:
        default_limit: Default number of results per search (default: 10).
        max_results: Maximum results to return from any source (default: 100).
        user_agent: User agent string for API requests.
        arxiv_delay: Seconds between arXiv API requests (default: 3.0).
        semanticscholar_api_key: Optional API key for Semantic Scholar.
        download_dir: Directory for downloaded PDFs (default: literature/pdfs).
        timeout: Request timeout in seconds (default: 30).
        bibtex_file: Path to BibTeX file (default: literature/references.bib).
        library_index_file: Path to JSON library index (default: literature/library.json).
        sources: List of enabled sources (default: arxiv, semanticscholar).
    
    Environment Variables:
        LITERATURE_DEFAULT_LIMIT: Override default_limit.
        LITERATURE_MAX_RESULTS: Override max_results.
        LITERATURE_USER_AGENT: Override user_agent.
        LITERATURE_ARXIV_DELAY: Override arxiv_delay.
        SEMANTICSCHOLAR_API_KEY: API key for Semantic Scholar.
        LITERATURE_DOWNLOAD_DIR: Override download_dir.
        LITERATURE_TIMEOUT: Override timeout.
        LITERATURE_BIBTEX_FILE: Override bibtex_file.
        LITERATURE_LIBRARY_INDEX: Override library_index_file.
        LITERATURE_SOURCES: Comma-separated list of sources.
    """
    
    # Search settings
    default_limit: int = 10
    max_results: int = 100
    user_agent: str = "Research-Template-Bot/1.0 (mailto:admin@example.com)"
    
    # API specific settings
    arxiv_delay: float = 3.0  # Seconds between requests
    semanticscholar_api_key: Optional[str] = None
    
    # PDF settings
    download_dir: str = "literature/pdfs"
    timeout: int = 30
    
    # Reference settings
    bibtex_file: str = "literature/references.bib"
    library_index_file: str = "literature/library.json"
    
    # Enabled sources (only arxiv and semanticscholar are implemented)
    sources: List[str] = field(default_factory=lambda: ["arxiv", "semanticscholar"])

    @classmethod
    def from_env(cls) -> LiteratureConfig:
        """Create configuration from environment variables.
        
        Reads configuration values from environment variables, falling back
        to defaults if not set.
        
        Returns:
            LiteratureConfig with values from environment or defaults.
        """
        # Parse sources from comma-separated string
        sources_str = os.environ.get("LITERATURE_SOURCES")
        sources = (
            [s.strip() for s in sources_str.split(",") if s.strip()]
            if sources_str
            else None
        )
        
        return cls(
            default_limit=int(os.environ.get("LITERATURE_DEFAULT_LIMIT", "10")),
            max_results=int(os.environ.get("LITERATURE_MAX_RESULTS", "100")),
            user_agent=os.environ.get(
                "LITERATURE_USER_AGENT",
                "Research-Template-Bot/1.0 (mailto:admin@example.com)"
            ),
            arxiv_delay=float(os.environ.get("LITERATURE_ARXIV_DELAY", "3.0")),
            semanticscholar_api_key=os.environ.get("SEMANTICSCHOLAR_API_KEY"),
            download_dir=os.environ.get("LITERATURE_DOWNLOAD_DIR", "literature/pdfs"),
            timeout=int(os.environ.get("LITERATURE_TIMEOUT", "30")),
            bibtex_file=os.environ.get("LITERATURE_BIBTEX_FILE", "literature/references.bib"),
            library_index_file=os.environ.get("LITERATURE_LIBRARY_INDEX", "literature/library.json"),
            sources=sources if sources else ["arxiv", "semanticscholar"],
        )

