# HTML Parsers Module - Complete Documentation

## Purpose

The HTML parsers module provides publisher-specific parsers for extracting PDF URLs from HTML landing pages.

## Components

### BaseHTMLParser (base.py)

Abstract base class for all parsers.

**Key Methods:**
- `extract_pdf_urls()` - Extract PDF URLs from HTML
- `can_parse()` - Check if parser can handle URL

### Publisher-Specific Parsers

- **ElsevierParser** (elsevier.py): Elsevier/ScienceDirect
- **SpringerParser** (springer.py): Springer
- **IEEEParser** (ieee.py): IEEE
- **ACMParser** (acm.py): ACM
- **WileyParser** (wiley.py): Wiley
- **GenericParser** (generic.py): Generic fallback

## Usage Examples

### Using Modular Parser

```python
from infrastructure.literature.html_parsers import extract_pdf_urls_modular

urls = extract_pdf_urls_modular(html_content, base_url)
```

### Using Specific Parser

```python
from infrastructure.literature.html_parsers import ElsevierParser

parser = ElsevierParser()
urls = parser.extract_pdf_urls(html_content, base_url)
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


