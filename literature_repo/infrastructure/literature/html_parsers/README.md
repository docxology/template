# HTML Parsers Module

Publisher-specific HTML parsers for PDF URL extraction.

## Components

- **base.py**: Base parser class
- **elsevier.py**: Elsevier/ScienceDirect parser
- **springer.py**: Springer parser
- **ieee.py**: IEEE parser
- **acm.py**: ACM parser
- **wiley.py**: Wiley parser
- **generic.py**: Generic fallback parser

## Quick Start

```python
from infrastructure.literature.html_parsers import extract_pdf_urls_modular

urls = extract_pdf_urls_modular(html_content, base_url)
```

## Features

- Publisher-specific parsing
- Automatic parser selection
- Generic fallback

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


