"""PDF handling and processing."""
from infrastructure.literature.pdf.handler import PDFHandler
from infrastructure.literature.pdf.downloader import PDFDownloader
from infrastructure.literature.pdf.extractor import (
    extract_pdf_urls_from_html,
    extract_citations,
)
from infrastructure.literature.pdf.fallbacks import (
    transform_pdf_url,
    doi_to_pdf_urls,
    PDFFallbackStrategies,
)

__all__ = [
    "PDFHandler",
    "PDFDownloader",
    "extract_pdf_urls_from_html",
    "extract_citations",
    "transform_pdf_url",
    "doi_to_pdf_urls",
    "PDFFallbackStrategies",
]


