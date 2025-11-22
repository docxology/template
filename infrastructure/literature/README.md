# Literature Search Module

Tools for searching papers, downloading PDFs, and managing citations.

## Features

- **Multi-source Search**: Unified search across arXiv and Semantic Scholar.
- **PDF Management**: Automatic downloading and organization.
- **Reference Management**: Auto-generation of BibTeX entries.
- **Deduplication**: Intelligent merging of results from multiple sources.

## Quick Start

```python
from infrastructure.literature import LiteratureSearch

# Initialize
searcher = LiteratureSearch()

# Search
papers = searcher.search("machine learning", limit=5)

# Process
for paper in papers:
    print(paper.title)
    if paper.pdf_url:
        searcher.download_paper(paper)
    searcher.add_to_library(paper)
```

