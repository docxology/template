"""PDF handling utilities for literature search."""
from __future__ import annotations

import os
import requests
from pathlib import Path
from typing import Optional

from infrastructure.core.exceptions import FileOperationError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.config import LiteratureConfig

logger = get_logger(__name__)


class PDFHandler:
    """Handles PDF downloading and text extraction."""

    def __init__(self, config: LiteratureConfig):
        self.config = config
        self._ensure_download_dir()

    def _ensure_download_dir(self) -> None:
        """Ensure download directory exists."""
        try:
            os.makedirs(self.config.download_dir, exist_ok=True)
        except OSError as e:
            raise FileOperationError(
                f"Failed to create download directory: {e}",
                context={"path": self.config.download_dir}
            )

    def download_pdf(self, url: str, filename: Optional[str] = None) -> Path:
        """Download PDF from URL.
        
        Args:
            url: URL to download from
            filename: Optional filename (default: derived from URL)
            
        Returns:
            Path to downloaded file
        """
        if not filename:
            filename = url.split('/')[-1]
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
        
        output_path = Path(self.config.download_dir) / filename
        
        if output_path.exists():
            logger.info(f"PDF already exists: {output_path}")
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

    def extract_citations(self, pdf_path: Path) -> list[str]:
        """Extract citations from PDF.
        
        Note: This is a placeholder for actual PDF parsing logic.
        Real implementation would use pypdf or similar.
        """
        if not pdf_path.exists():
            raise FileOperationError("PDF file not found", context={"path": str(pdf_path)})
            
        logger.warning(f"Citation extraction not implemented for {pdf_path}")
        return []

