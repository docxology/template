"""Configuration management for the literature search module."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LiteratureConfig:
    """Configuration for literature search."""
    
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
    
    # Enabled sources
    sources: List[str] = field(default_factory=lambda: ["arxiv", "semanticscholar", "crossref", "pubmed"])

    @classmethod
    def from_env(cls) -> LiteratureConfig:
        """Create configuration from environment variables."""
        # This would be implemented to load from os.environ
        return cls()

