"""PDF handling utilities for literature search."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

from infrastructure.core.exceptions import FileOperationError, LiteratureSearchError
from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.core.config import LiteratureConfig
from infrastructure.literature.sources import SearchResult
from infrastructure.literature.pdf.fallbacks import (
    transform_pdf_url,
    doi_to_pdf_urls,
    PDFFallbackStrategies,
)
from infrastructure.literature.pdf.downloader import PDFDownloader
from infrastructure.literature.pdf.extractor import (
    extract_pdf_urls_from_html,
    extract_citations,
)

if TYPE_CHECKING:
    from infrastructure.literature.library.index import LibraryIndex

logger = get_logger(__name__)


class PDFHandler:
    """Handles PDF downloading and text extraction.
    
    Downloads PDFs using citation keys as filenames for consistency
    with the BibTeX and library index. Supports retry logic, User-Agent
    rotation, and multiple fallback strategies for failed downloads:
    
    Fallback Order:
    1. Primary URL (from search result)
    2. Transformed URLs (PMC variants, arXiv, bioRxiv patterns)
    3. Unpaywall lookup (open access versions)
    4. arXiv title search (find preprint by title)
    5. bioRxiv/medRxiv DOI lookup (find preprint by DOI)
    """

    def __init__(self, config: LiteratureConfig, library_index: Optional["LibraryIndex"] = None):
        """Initialize PDF handler.
        
        Args:
            config: Literature configuration.
            library_index: Optional LibraryIndex for citation key generation and tracking.
        """
        self.config = config
        self._library_index = library_index
        
        # Initialize downloader
        self._downloader = PDFDownloader(config)
        
        # Initialize fallback strategies
        self._fallbacks = PDFFallbackStrategies(config)
        
        # Ensure download directory exists
        self._downloader._ensure_download_dir()

    def _normalize_arxiv_pdf_url(self, url: str) -> str:
        """Normalize arXiv PDF URL to ensure correct format.
        
        Ensures arXiv PDF URLs use the correct format (arxiv.org/pdf/ID.pdf)
        and removes version suffixes.
        
        Args:
            url: arXiv URL (can be abstract or PDF URL).
            
        Returns:
            Normalized arXiv PDF URL.
        """
        import re
        # Extract arXiv ID from various URL formats
        arxiv_match = re.search(r'arxiv\.org/(?:abs|pdf)/((?:\d{4}\.\d{4,5})|(?:\w+-\w+/\d{7}))(?:v\d+)?', url)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            # Return normalized PDF URL (remove version suffix)
            return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        return url

    def _get_download_timeout(self, source: Optional[str] = None) -> float:
        """Get appropriate timeout for PDF download based on source.
        
        Args:
            source: Source name (e.g., 'arxiv', 'semanticscholar').
            
        Returns:
            Timeout value in seconds.
        """
        if source and source in self.config.source_configs:
            source_timeout = self.config.source_configs[source].get("timeout")
            if source_timeout:
                return source_timeout
        
        # Fall back to PDF-specific timeout or general timeout
        return getattr(self.config, 'pdf_download_timeout', self.config.timeout)

    def _prioritize_urls_by_source(self, urls: List[str], source: Optional[str] = None) -> List[str]:
        """Reorder URLs based on source to prioritize most reliable sources.
        
        For arXiv sources, prioritizes direct arXiv PDF URLs.
        
        Args:
            urls: List of URLs to prioritize.
            source: Source name (e.g., 'arxiv').
            
        Returns:
            Reordered list with prioritized URLs first.
        """
        if not source or not urls:
            return urls
        
        if source == "arxiv":
            # Separate arXiv PDF URLs from others
            arxiv_pdf_urls = []
            other_urls = []
            
            for url in urls:
                if 'arxiv.org/pdf/' in url or 'export.arxiv.org/pdf/' in url:
                    # Normalize arXiv URL
                    normalized = self._normalize_arxiv_pdf_url(url)
                    if normalized not in arxiv_pdf_urls:
                        arxiv_pdf_urls.append(normalized)
                else:
                    other_urls.append(url)
            
            # Return arXiv URLs first, then others
            return arxiv_pdf_urls + other_urls
        
        # For other sources, return as-is
        return urls

    def set_library_index(self, library_index: "LibraryIndex") -> None:
        """Set the library index for coordinated operations.

        Args:
            library_index: LibraryIndex instance to use.
        """
        self._library_index = library_index

    def parse_html_for_pdf(self, html_content: bytes, base_url: str) -> List[str]:
        """Parse HTML content to extract PDF URLs using modular parser system.

        Automatically detects publisher and uses appropriate parser for best results.

        Args:
            html_content: Raw HTML content as bytes.
            base_url: Base URL for resolving relative links.

        Returns:
            List of candidate PDF URLs found in HTML.
        """
        try:
            from infrastructure.literature.html_parsers import extract_pdf_urls_modular
            return extract_pdf_urls_modular(html_content, base_url)
        except ImportError:
            # Fallback to original implementation
            return extract_pdf_urls_from_html(html_content, base_url)

    def download_pdf(
        self,
        url: Optional[str],
        filename: Optional[str] = None,
        result: Optional[SearchResult] = None
    ) -> Path:
        """Download PDF from URL with enhanced retry logic and fallback strategies.

        Attempts to download with exponential backoff retry and multiple fallback strategies.
        For 403 Forbidden errors, tries alternative User-Agents and request methods.
        If configured, will try Unpaywall as fallback when primary download fails.

        Args:
            url: URL to download from.
            filename: Optional filename (default: derived from result or URL).
            result: Optional SearchResult for citation key naming.

        Returns:
            Path to downloaded file.

        Raises:
            LiteratureSearchError: If all download attempts fail.
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
                filename = url.split('/')[-1] if url else "unknown.pdf"
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'

        output_path = Path(self.config.download_dir) / filename

        if output_path.exists():
            logger.info(f"PDF already exists: {output_path}")
            # Update library index with path if available
            if result and self._library_index:
                citation_key = filename.replace('.pdf', '')
                self._library_index.update_pdf_path(citation_key, str(output_path))
            return output_path

        # Build list of URLs to try (primary + transformed + Unpaywall fallback)
        urls_to_try: List[str] = []
        attempted_urls: List[str] = []
        last_error: Optional[Exception] = None
        last_failure_reason: Optional[str] = None
        
        # Get source for prioritization and timeout
        source = result.source if result else None

        # Handle case where no primary URL is provided
        if url is None:
            logger.debug("No primary URL provided, using fallback strategies only")
        else:
            # For arXiv sources, prioritize arXiv PDF URL directly
            if source == "arxiv" and result and result.pdf_url:
                # Normalize and prioritize arXiv PDF URL
                arxiv_pdf_url = self._normalize_arxiv_pdf_url(result.pdf_url)
                urls_to_try.append(arxiv_pdf_url)
                logger.debug(f"Prioritizing arXiv PDF URL: {arxiv_pdf_url}")
                
                # Add transformed URLs as fallback (but arXiv PDF should work)
                transformed_urls = transform_pdf_url(url)
                for transformed_url in transformed_urls:
                    if transformed_url not in urls_to_try and 'arxiv.org/pdf/' in transformed_url:
                        urls_to_try.append(transformed_url)
            else:
                # Add transformed URLs (multiple candidates for PMC, etc.)
                transformed_urls = transform_pdf_url(url)

                # For URLs that look like abstract pages, prioritize transformed versions
                if transformed_urls and ('abs' in url.lower() or 'abstract' in url.lower()):
                    # For abstract URLs, try transformed versions first
                    urls_to_try.extend(transformed_urls)
                    if url not in urls_to_try:
                        urls_to_try.append(url)  # Add original as fallback
                    logger.debug(f"Prioritizing transformed URLs for abstract URL: {url}")
                else:
                    # For direct PDF URLs or unknown patterns, try original first
                    urls_to_try.append(url)
                    for transformed_url in transformed_urls:
                        if transformed_url not in urls_to_try:
                            logger.debug(f"Adding transformed PDF URL: {transformed_url}")
                            urls_to_try.append(transformed_url)

        # Add DOI-based PDF URLs if DOI is available
        if result and result.doi:
            doi_urls = doi_to_pdf_urls(result.doi)
            for doi_url in doi_urls:
                if doi_url not in urls_to_try:
                    logger.debug(f"Adding DOI-based PDF URL: {doi_url}")
                    urls_to_try.append(doi_url)

        # Add Unpaywall fallback if configured and DOI available
        # Skip Unpaywall for arXiv sources (arXiv PDFs are always available)
        if result and result.doi and source != "arxiv":
            unpaywall_url = self._fallbacks.get_unpaywall_url(result.doi)
            if unpaywall_url and unpaywall_url not in urls_to_try:
                logger.debug(f"Adding Unpaywall fallback URL: {unpaywall_url}")
                urls_to_try.append(unpaywall_url)

        # Prioritize URLs based on source
        urls_to_try = self._prioritize_urls_by_source(urls_to_try, source)
        
        # Get appropriate timeout for this source
        download_timeout = self._get_download_timeout(source)
        logger.debug(f"Using timeout {download_timeout}s for source: {source or 'unknown'}")

        # Try each URL with enhanced retry logic including 403 error recovery
        primary_urls_failed = False
        if urls_to_try:
            for try_url in urls_to_try:
                download_result = self._downloader.download_with_enhanced_retry(
                    try_url,
                    output_path,
                    parse_html_callback=self.parse_html_for_pdf,
                    timeout=download_timeout
                )
                attempted_urls.extend(download_result[3])  # Add all attempted URLs

                if download_result[0]:  # Success
                    # Log file size and location
                    try:
                        file_size = output_path.stat().st_size
                        logger.info(f"Downloaded: {filename} ({file_size:,} bytes) -> {output_path}")
                    except Exception as e:
                        logger.warning(f"Could not get file size for {output_path}: {e}")

                    # Update library index with path
                    if result and self._library_index:
                        citation_key = filename.replace('.pdf', '')
                        self._library_index.update_pdf_path(citation_key, str(output_path))
                    return output_path
                else:
                    last_error = download_result[1]
                    last_failure_reason = download_result[2]
                    logger.debug(f"Download failed from {try_url}: {last_failure_reason}")
                    primary_urls_failed = True
        else:
            # No primary URLs provided, go directly to fallbacks
            primary_urls_failed = True
            logger.debug("No primary URLs provided, attempting fallback strategies")

        # Primary URLs failed or none provided - try preprint server fallbacks
        # These are more expensive (require API calls), so only used after URL-based attempts fail
        
        # Fallback 4: arXiv title search (skip if source is already arXiv)
        if result and result.title and source != "arxiv":
            arxiv_result = self._fallbacks.get_arxiv_fallback(result)
            if arxiv_result:
                attempted_urls.append(f"arXiv title search: {arxiv_result}")
                download_result = self._downloader.download_with_enhanced_retry(
                    arxiv_result,
                    output_path,
                    parse_html_callback=self.parse_html_for_pdf,
                    timeout=self._get_download_timeout("arxiv")
                )
                attempted_urls.extend(download_result[3])
                
                if download_result[0]:
                    try:
                        file_size = output_path.stat().st_size
                        logger.info(f"Downloaded via arXiv fallback: {filename} ({file_size:,} bytes)")
                    except Exception:
                        pass
                    
                    if result and self._library_index:
                        citation_key = filename.replace('.pdf', '')
                        self._library_index.update_pdf_path(citation_key, str(output_path))
                    return output_path
                else:
                    last_error = download_result[1]
                    last_failure_reason = download_result[2]
        
        # Fallback 5: bioRxiv/medRxiv DOI lookup
        if result and result.doi:
            biorxiv_result = self._fallbacks.get_biorxiv_fallback(result)
            if biorxiv_result:
                attempted_urls.append(f"bioRxiv/medRxiv DOI lookup: {biorxiv_result}")
                download_result = self._downloader.download_with_enhanced_retry(
                    biorxiv_result,
                    output_path,
                    parse_html_callback=self.parse_html_for_pdf,
                    timeout=self._get_download_timeout("biorxiv")
                )
                attempted_urls.extend(download_result[3])
                
                if download_result[0]:
                    try:
                        file_size = output_path.stat().st_size
                        logger.info(f"Downloaded via bioRxiv fallback: {filename} ({file_size:,} bytes)")
                    except Exception:
                        pass
                    
                    if result and self._library_index:
                        citation_key = filename.replace('.pdf', '')
                        self._library_index.update_pdf_path(citation_key, str(output_path))
                    return output_path
                else:
                    last_error = download_result[1]
                    last_failure_reason = download_result[2]

        # All attempts failed
        error_msg = f"Failed to download PDF after trying {len(urls_to_try)} URL(s) plus fallbacks"
        if last_error:
            error_msg = f"{error_msg}: {last_error}"

        raise LiteratureSearchError(
            error_msg,
            context={
                "attempted_urls": attempted_urls,
                "output_path": str(output_path),
                "failure_reason": last_failure_reason
            }
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

    def extract_citations(self, pdf_path: Path) -> List[str]:
        """Extract citations from PDF.
        
        Note: This is a placeholder for actual PDF parsing logic.
        Real implementation would use pypdf or similar.
        
        Args:
            pdf_path: Path to PDF file.
            
        Returns:
            List of extracted citations (empty for now).
        """
        return extract_citations(pdf_path)
