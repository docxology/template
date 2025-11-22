"""Reference management for literature search."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Optional

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import SearchResult

logger = get_logger(__name__)


class ReferenceManager:
    """Manages references and BibTeX generation."""

    def __init__(self, config: LiteratureConfig):
        self.config = config

    def add_reference(self, result: SearchResult) -> str:
        """Add paper to references.
        
        Returns:
            BibTeX citation key
        """
        key = self._generate_key(result)
        bib_entry = self._format_bibtex(result, key)
        
        self._append_to_bibtex(bib_entry)
        return key

    def _generate_key(self, result: SearchResult) -> str:
        """Generate BibTeX key (AuthorYearTitle)."""
        author = result.authors[0].split()[-1].lower() if result.authors else "anonymous"
        year = str(result.year) if result.year else "nodate"
        title_word = result.title.split()[0].lower()
        # Sanitize
        author = "".join(c for c in author if c.isalnum())
        title_word = "".join(c for c in title_word if c.isalnum())
        return f"{author}{year}{title_word}"

    def _format_bibtex(self, result: SearchResult, key: str) -> str:
        """Format result as BibTeX entry."""
        entry_type = "article"
        
        fields = [
            f"  title={{{result.title}}}",
            f"  author={{{' and '.join(result.authors)}}}",
            f"  year={{{result.year}}}" if result.year else None,
            f"  url={{{result.url}}}",
            f"  abstract={{{result.abstract}}}" if result.abstract else None,
            f"  doi={{{result.doi}}}" if result.doi else None,
            f"  journal={{{result.venue}}}" if result.venue else None
        ]
        
        fields_str = ",\n".join(f for f in fields if f)
        return f"@{entry_type}{{{key},\n{fields_str}\n}}\n"

    def _append_to_bibtex(self, entry: str) -> None:
        """Append entry to BibTeX file."""
        path = Path(self.config.bibtex_file)
        
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if duplicate (simplistic check)
            if path.exists():
                content = path.read_text()
                # Extract key from entry
                key = entry.split(',')[0].split('{')[1]
                if key in content:
                    logger.info(f"Reference {key} already exists")
                    return

            with open(path, 'a') as f:
                f.write(entry + "\n")
                
        except OSError as e:
            raise FileOperationError(
                f"Failed to update BibTeX file: {e}",
                context={"path": str(path)}
            )

