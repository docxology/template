# Literature Search Module

Tools for searching papers, downloading PDFs, and managing citations.

## Features

- **Multi-source Search**: Unified search across arXiv and Semantic Scholar
- **PDF Management**: Automatic downloading with citation key naming
- **HTML Parsing**: Automatic PDF URL extraction from publisher landing pages
- **Enhanced Logging**: Structured progress tracking with timing and statistics
- **Reference Management**: BibTeX generation with deduplication
- **Library Index**: JSON-based tracking of all papers with metadata
- **Environment Configuration**: Load settings from environment variables
- **CLI Interface**: Command-line search, download, and library management

## Output Files

```
literature/
├── references.bib    # BibTeX entries
├── library.json      # JSON index with full metadata
└── pdfs/             # Downloaded PDFs
    └── author2024title.pdf
```

## Quick Start

```python
from infrastructure.literature import LiteratureSearch

# Initialize
searcher = LiteratureSearch()

# Search
papers = searcher.search("machine learning", limit=5)

# Process results
for paper in papers:
    print(f"{paper.title} ({paper.year})")
    
    # Add to library (BibTeX + JSON)
    citation_key = searcher.add_to_library(paper)
    
    # Download PDF (named as citation_key.pdf)
    if paper.pdf_url:
        searcher.download_paper(paper)

# Get library stats
stats = searcher.get_library_stats()
print(f"Total papers: {stats['total_entries']}")
```

## CLI Usage

```bash
# Basic search (adds to library automatically)
python3 -m infrastructure.literature.cli search "deep learning"

# Search with options
python3 -m infrastructure.literature.cli search "transformers" \
    --limit 20 \
    --sources arxiv,semanticscholar \
    --download

# List papers in library
python3 -m infrastructure.literature.cli library list

# Show library statistics
python3 -m infrastructure.literature.cli library stats

# Export library
python3 -m infrastructure.literature.cli library export --output export.json

# NEW: Clean up library
python3 scripts/07_literature_search.py --cleanup

# NEW: Advanced LLM operations
python3 scripts/07_literature_search.py --llm-operation review
python3 scripts/07_literature_search.py --llm-operation communication
python3 scripts/07_literature_search.py --llm-operation compare
```

## Configuration

### Environment Variables

```bash
export LITERATURE_DEFAULT_LIMIT=20
export LITERATURE_DOWNLOAD_DIR=/path/to/pdfs
export LITERATURE_LIBRARY_INDEX=/path/to/library.json
export SEMANTICSCHOLAR_API_KEY=your-api-key
```

### Programmatic

```python
from infrastructure.literature import LiteratureConfig

config = LiteratureConfig(
    download_dir="custom/pdfs",
    bibtex_file="custom/refs.bib",
    library_index_file="custom/library.json"
)
searcher = LiteratureSearch(config)

# Or load from environment
config = LiteratureConfig.from_env()
```

## Public API

```python
from infrastructure.literature import (
    LiteratureSearch,        # Main search interface
    LiteratureConfig,        # Configuration dataclass
    SearchResult,            # Search result dataclass
    PDFHandler,              # PDF download handler
    ReferenceManager,        # BibTeX management
    LibraryIndex,            # JSON library index
    LibraryEntry,            # Library entry dataclass
    SummarizationEngine,     # Paper summarization (main interface)
    PaperSummarizer,         # Alias for SummarizationEngine (backward compatibility)
    SummaryQualityValidator, # Summary quality validation
    SummarizationResult,     # Summarization result dataclass
    LiteratureWorkflow,      # High-level workflow orchestration
)
```

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed documentation
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure overview
