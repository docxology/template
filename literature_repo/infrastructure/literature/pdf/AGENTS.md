# PDF Module - Complete Documentation

## Purpose

The PDF module handles all aspects of PDF downloading, text extraction, and URL resolution with comprehensive fallback strategies.

## Components

### PDFHandler (handler.py)

Main interface for PDF downloading and management.

**Key Methods:**
- `download_paper()` - Download PDF for a search result
- `download_pdf()` - Download PDF from URL with citation key naming

**Features:**
- Automatic retry with exponential backoff
- User-Agent rotation
- Multiple fallback strategies
- Citation key-based file naming

### PDFDownloader (downloader.py)

Low-level PDF download implementation.

**Features:**
- Content type validation
- HTML response detection
- Recursive HTML parsing (limited depth)
- Error categorization

### PDF Extractor (extractor.py)

Text extraction and HTML parsing utilities.

**Functions:**
- `extract_pdf_urls_from_html()` - Extract PDF URLs from HTML content
- `extract_citations()` - Extract citations from PDF (placeholder)

### PDF Fallbacks (fallbacks.py)

Fallback strategies for PDF URL resolution.

**Strategies:**
- URL transformation (PMC, arXiv, bioRxiv patterns)
- Unpaywall lookup
- DOI-based URL generation
- Publisher-specific patterns

## Usage Examples

### Basic Download

```python
from infrastructure.literature.pdf import PDFHandler
from infrastructure.literature.core import LiteratureConfig

config = LiteratureConfig()
handler = PDFHandler(config)

pdf_path = handler.download_paper(search_result)
```

### Fallback Strategies

The handler automatically tries multiple strategies:
1. Primary URL from search result
2. Transformed URLs (PMC variants, etc.)
3. Unpaywall lookup
4. arXiv title search
5. bioRxiv/medRxiv DOI lookup

## Error Handling

PDF downloads categorize failures:
- `access_denied` - HTTP 403 Forbidden
- `not_found` - HTTP 404 Not Found
- `html_response` - HTML received instead of PDF
- `timeout` - Request timeout
- `network_error` - Connection errors

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


