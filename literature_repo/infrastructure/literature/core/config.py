"""Configuration management for the literature search module."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# Browser-like User-Agent strings for PDF downloads
BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


@dataclass
class LiteratureConfig:
    """Configuration for literature search.
    
    Attributes:
        default_limit: Default number of results per source per search (default: 25).
        max_results: Maximum results to return from any source (default: 100).
        user_agent: User agent string for API requests.
        arxiv_delay: Seconds between arXiv API requests (default: 3.0).
        semanticscholar_delay: Seconds between Semantic Scholar requests (default: 1.5).
        semanticscholar_api_key: Optional API key for Semantic Scholar.
        retry_attempts: Number of retry attempts for failed requests (default: 3).
        retry_delay: Base delay for exponential backoff in seconds (default: 5.0).
        download_dir: Directory for downloaded PDFs (default: data/pdfs).
        timeout: Request timeout in seconds (default: 30.0).
        pdf_download_timeout: Timeout for PDF downloads in seconds (default: 60.0).
        bibtex_file: Path to BibTeX file (default: data/references.bib).
        library_index_file: Path to JSON library index (default: data/library.json).
        sources: List of enabled sources (default: arxiv, semanticscholar).
        use_unpaywall: Enable Unpaywall API for open access PDF fallback (default: False).
        unpaywall_email: Email for Unpaywall API (required if use_unpaywall is True).
        download_retry_attempts: Retry attempts for PDF downloads (default: 2).
        download_retry_delay: Base delay for download retry in seconds (default: 2.0).
        use_browser_user_agent: Use browser-like User-Agent for downloads (default: True).
    
    Environment Variables:
        LITERATURE_DEFAULT_LIMIT: Override default_limit.
        LITERATURE_MAX_RESULTS: Override max_results.
        LITERATURE_USER_AGENT: Override user_agent.
        LITERATURE_ARXIV_DELAY: Override arxiv_delay.
        LITERATURE_SEMANTICSCHOLAR_DELAY: Override semanticscholar_delay.
        SEMANTICSCHOLAR_API_KEY: API key for Semantic Scholar.
        LITERATURE_RETRY_ATTEMPTS: Override retry_attempts.
        LITERATURE_RETRY_DELAY: Override retry_delay.
        LITERATURE_DOWNLOAD_DIR: Override download_dir.
        LITERATURE_TIMEOUT: Override timeout.
        LITERATURE_PDF_DOWNLOAD_TIMEOUT: Override pdf_download_timeout.
        LITERATURE_BIBTEX_FILE: Override bibtex_file.
        LITERATURE_LIBRARY_INDEX: Override library_index_file.
        LITERATURE_SOURCES: Comma-separated list of sources (available: arxiv, semanticscholar, biorxiv, pubmed, europepmc, crossref, openalex, dblp).
        LITERATURE_USE_UNPAYWALL: Enable Unpaywall (true/false).
        UNPAYWALL_EMAIL: Email for Unpaywall API.
        LITERATURE_DOWNLOAD_RETRY_ATTEMPTS: Override download_retry_attempts.
        LITERATURE_DOWNLOAD_RETRY_DELAY: Override download_retry_delay.
        LITERATURE_USE_BROWSER_USER_AGENT: Use browser User-Agent (true/false).
    """
    
    # Search settings
    default_limit: int = 25  # Increased for better coverage
    max_results: int = 100
    user_agent: str = "Research-Template-Bot/1.0 (mailto:admin@example.com)"
    
    # API specific settings
    arxiv_delay: float = 3.0  # Seconds between arXiv requests
    semanticscholar_delay: float = 1.5  # Seconds between Semantic Scholar requests
    semanticscholar_api_key: Optional[str] = None
    retry_attempts: int = 3  # Retry failed requests
    retry_delay: float = 5.0  # Base delay for exponential backoff
    
    # Per-source configuration (can be extended for other sources)
    source_configs: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "arxiv": {
            "delay": 3.0,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        },
        "semanticscholar": {
            "delay": 1.5,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True,
            "rate_limit_strategy": "exponential_backoff"
        },
        "pubmed": {
            "delay": 0.34,  # ~3 requests/second (NCBI requirement)
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        },
        "europepmc": {
            "delay": 0.5,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        },
        "crossref": {
            "delay": 1.0,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        },
        "openalex": {
            "delay": 0.5,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        },
        "dblp": {
            "delay": 1.0,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        },
        "biorxiv": {
            "delay": 1.0,
            "max_retries": 3,
            "timeout": 30.0,
            "health_check_enabled": True
        }
    })
    
    # PDF settings
    download_dir: str = "data/pdfs"
    timeout: float = 30.0  # General request timeout (matching source_configs)
    pdf_download_timeout: float = 60.0  # Timeout for PDF downloads (larger files need more time)
    
    # Reference settings
    bibtex_file: str = "data/references.bib"
    library_index_file: str = "data/library.json"
    
    # Enabled sources
    # Available sources: arxiv, semanticscholar, biorxiv, pubmed, europepmc, crossref, openalex, dblp, unpaywall
    # Note: unpaywall requires use_unpaywall=True and unpaywall_email
    # Note: biorxiv is available but may have limited search capabilities
    sources: List[str] = field(default_factory=lambda: [
        "arxiv", 
        "semanticscholar", 
        "biorxiv",
        "pubmed",
        "europepmc",
        "crossref",
        "openalex",
        "dblp"
    ])
    
    # Unpaywall integration (optional - for open access fallback)
    use_unpaywall: bool = True  # Enable by default
    unpaywall_email: str = "research@4dresearch.com"  # Default email for Unpaywall API access
    
    # PDF download retry settings
    download_retry_attempts: int = 2
    download_retry_delay: float = 2.0
    
    # Use browser-like User-Agent for PDF downloads (helps avoid 403 errors)
    use_browser_user_agent: bool = True

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
        
        # Parse boolean environment variables
        use_unpaywall_str = os.environ.get("LITERATURE_USE_UNPAYWALL", "true").lower()
        use_unpaywall = use_unpaywall_str in ("true", "1", "yes")

        use_browser_ua_str = os.environ.get("LITERATURE_USE_BROWSER_USER_AGENT", "true").lower()
        use_browser_user_agent = use_browser_ua_str in ("true", "1", "yes")
        
        return cls(
            default_limit=int(os.environ.get("LITERATURE_DEFAULT_LIMIT", "25")),
            max_results=int(os.environ.get("LITERATURE_MAX_RESULTS", "100")),
            user_agent=os.environ.get(
                "LITERATURE_USER_AGENT",
                "Research-Template-Bot/1.0 (mailto:admin@example.com)"
            ),
            arxiv_delay=float(os.environ.get("LITERATURE_ARXIV_DELAY", "3.0")),
            semanticscholar_delay=float(os.environ.get("LITERATURE_SEMANTICSCHOLAR_DELAY", "1.5")),
            semanticscholar_api_key=os.environ.get("SEMANTICSCHOLAR_API_KEY"),
            retry_attempts=int(os.environ.get("LITERATURE_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.environ.get("LITERATURE_RETRY_DELAY", "5.0")),
            download_dir=os.environ.get("LITERATURE_DOWNLOAD_DIR", "data/pdfs"),
            timeout=float(os.environ.get("LITERATURE_TIMEOUT", "30.0")),
            pdf_download_timeout=float(os.environ.get("LITERATURE_PDF_DOWNLOAD_TIMEOUT", "60.0")),
            bibtex_file=os.environ.get("LITERATURE_BIBTEX_FILE", "data/references.bib"),
            library_index_file=os.environ.get("LITERATURE_LIBRARY_INDEX", "data/library.json"),
            sources=sources if sources else [
                "arxiv", 
                "semanticscholar", 
                "biorxiv",
                "pubmed",
                "europepmc",
                "crossref",
                "openalex",
                "dblp"
            ],
            use_unpaywall=use_unpaywall,
            unpaywall_email=os.environ.get("UNPAYWALL_EMAIL", "research@4dresearch.com"),
            download_retry_attempts=int(os.environ.get("LITERATURE_DOWNLOAD_RETRY_ATTEMPTS", "2")),
            download_retry_delay=float(os.environ.get("LITERATURE_DOWNLOAD_RETRY_DELAY", "2.0")),
            use_browser_user_agent=use_browser_user_agent,
        )

