"""PDF handling utilities for literature search."""
from __future__ import annotations

import os
import requests
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from infrastructure.core.exceptions import FileOperationError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.config import LiteratureConfig
from infrastructure.literature.api import SearchResult

if TYPE_CHECKING:
    from infrastructure.literature.library_index import LibraryIndex

logger = get_logger(__name__)


class PDFHandler:
    """Handles PDF downloading and text extraction.
    
    Downloads PDFs using citation keys as filenames for consistency
    with the BibTeX and library index.
    """

    def __init__(self, config: LiteratureConfig, library_index: Optional["LibraryIndex"] = None):
        """Initialize PDF handler.
        
        Args:
            config: Literature configuration.
            library_index: Optional LibraryIndex for citation key generation and tracking.
        """
        self.config = config
        self._library_index = library_index
        self._ensure_download_dir()

    def set_library_index(self, library_index: "LibraryIndex") -> None:
        """Set the library index for coordinated operations.
        
        Args:
            library_index: LibraryIndex instance to use.
        """
        self._library_index = library_index

    def _ensure_download_dir(self) -> None:
        """Ensure download directory exists."""
        try:
            os.makedirs(self.config.download_dir, exist_ok=True)
        except OSError as e:
            raise FileOperationError(
                f"Failed to create download directory: {e}",
                context={"path": self.config.download_dir}
            )

    def download_pdf(
        self, 
        url: str, 
        filename: Optional[str] = None,
        result: Optional[SearchResult] = None
    ) -> Path:
        """Download PDF from URL.
        
        Args:
            url: URL to download from.
            filename: Optional filename (default: derived from result or URL).
            result: Optional SearchResult for citation key naming.
            
        Returns:
            Path to downloaded file.
        """
        # Determine filename
        if not filename:
            if result and self._library_index:
                # Use citation key as filename
                citation_key = self._library_index.generate_citation_key(
                    result.title, result.authors, result.year
                )
                filename = f"{citation_key}.pdf"
            elif result:
                # Generate key locally
                filename = self._generate_filename_from_result(result)
            else:
                # Fall back to URL-based naming
                filename = url.split('/')[-1]
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
        
        output_path = Path(self.config.download_dir) / filename
        
        if output_path.exists():
            logger.info(f"PDF already exists: {output_path}")
            # Update library index with path if available
            if result and self._library_index:
                citation_key = filename.replace('.pdf', '')
                # Use string path directly (already relative to project root)
                self._library_index.update_pdf_path(citation_key, str(output_path))
            return output_path
            
        logger.info(f"Downloading PDF from {url} to {output_path}")
        
        try:
            response = requests.get(
                url, 
                stream=True, 
                timeout=self.config.timeout,
                headers={"User-Agent": self.config.user_agent}
            )
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Update library index with path
            if result and self._library_index:
                citation_key = filename.replace('.pdf', '')
                # Use string path directly (already relative to project root)
                self._library_index.update_pdf_path(citation_key, str(output_path))
                    
            return output_path
            
        except requests.exceptions.RequestException as e:
            raise LiteratureSearchError(
                f"Failed to download PDF: {e}",
                context={"url": url, "output_path": str(output_path)}
            )
        except OSError as e:
            raise FileOperationError(
                f"Failed to write PDF file: {e}",
                context={"path": str(output_path)}
            )

    def _generate_filename_from_result(self, result: SearchResult) -> str:
        """Generate filename from search result using citation key format.
        
        Args:
            result: Search result.
            
        Returns:
            Filename string with .pdf extension.
        """
        # Get first author's last name
        if result.authors:
            first_author = result.authors[0]
            parts = first_author.replace(",", " ").split()
            author = parts[-1].lower() if parts else "anonymous"
        else:
            author = "anonymous"
        
        # Sanitize
        author = "".join(c for c in author if c.isalnum())
        
        year = str(result.year) if result.year else "nodate"
        
        # First significant word from title
        title_words = result.title.lower().split()
        skip_words = {"a", "an", "the", "on", "in", "of", "for", "to", "and", "with"}
        title_word = "paper"
        for word in title_words:
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word and clean_word not in skip_words:
                title_word = clean_word
                break
        
        return f"{author}{year}{title_word}.pdf"

    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result.
        
        Convenience method that extracts pdf_url from result.
        
        Args:
            result: Search result with pdf_url.
            
        Returns:
            Path to downloaded file, or None if no PDF URL.
        """
        if not result.pdf_url:
            logger.warning(f"No PDF URL for paper: {result.title}")
            return None
        
        return self.download_pdf(result.pdf_url, result=result)

    def extract_citations(self, pdf_path: Path) -> list[str]:
        """Extract citations from PDF.
        
        Note: This is a placeholder for actual PDF parsing logic.
        Real implementation would use pypdf or similar.
        
        Args:
            pdf_path: Path to PDF file.
            
        Returns:
            List of extracted citations (empty for now).
        """
        if not pdf_path.exists():
            raise FileOperationError("PDF file not found", context={"path": str(pdf_path)})
            
        logger.warning(f"Citation extraction not implemented for {pdf_path}")
        return []
