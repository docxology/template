# Literature Search and Management System

Standalone repository for academic literature search, PDF management, reference tracking, and AI-powered paper summarization.

## Features

- **Multi-Source Search**: Unified search across arXiv, Semantic Scholar, PubMed, CrossRef, OpenAlex, DBLP, and more
- **PDF Management**: Automatic downloading with citation key naming and open access fallback
- **Reference Management**: BibTeX generation with deduplication and library indexing
- **AI Summarization**: Local LLM-powered paper summarization with quality validation
- **Meta-Analysis**: PCA, keyword analysis, temporal trends, and visualization tools
- **Library Tracking**: JSON-based index with complete metadata and progress tracking

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd literature

# Install dependencies
uv sync
# or
pip install -e .
```

### Basic Usage

```bash
# Interactive menu
./run_literature.sh

# Search for papers
python3 scripts/07_literature_search.py --search --keywords "machine learning,deep learning"

# Download PDFs for existing entries
python3 scripts/07_literature_search.py --download-only

# Generate summaries (requires Ollama)
python3 scripts/07_literature_search.py --summarize

# Meta-analysis pipeline
python3 scripts/07_literature_search.py --meta-analysis --keywords "optimization"
```

### Python API

```python
from infrastructure.literature import LiteratureSearch, LiteratureConfig

# Initialize
config = LiteratureConfig.from_env()
searcher = LiteratureSearch(config)

# Search
papers = searcher.search("machine learning", limit=10)

# Process results
for paper in papers:
    print(f"{paper.title} ({paper.year})")
    
    # Add to library (BibTeX + JSON)
    citation_key = searcher.add_to_library(paper)
    
    # Download PDF
    if paper.pdf_url:
        result = searcher.download_paper(paper)
        print(f"  PDF: {result.status}")
```

## Directory Structure

```
literature/
├── run_literature.sh          # Main orchestrator script
├── scripts/                    # Orchestrator scripts
│   ├── 07_literature_search.py
│   └── bash_utils.sh
├── infrastructure/             # Core modules
│   ├── core/                   # Foundation utilities
│   ├── llm/                    # LLM integration
│   └── literature/             # Literature search modules
├── tests/                      # Test suite
│   └── infrastructure/
├── data/                       # Data directory
│   ├── library.json            # Paper metadata index
│   ├── references.bib          # BibTeX bibliography
│   ├── pdfs/                   # Downloaded PDFs
│   ├── summaries/              # AI-generated summaries
│   ├── extracted_text/         # Extracted PDF text
│   └── output/                 # Meta-analysis outputs
└── docs/                       # Documentation
```

## Output Files

All outputs are saved to the `data/` directory:

- **`data/library.json`** - JSON index with complete paper metadata
- **`data/references.bib`** - BibTeX entries for citations
- **`data/pdfs/`** - Downloaded PDFs (named by citation key)
- **`data/summaries/`** - AI-generated paper summaries
- **`data/extracted_text/`** - Extracted text from PDFs
- **`data/output/`** - Meta-analysis visualizations and reports

## Requirements

- Python >= 3.10
- Ollama (for AI summarization) - optional but recommended
- Internet connection (for API searches and PDF downloads)

## Configuration

Configuration is managed via environment variables:

```bash
# Search settings
export LITERATURE_DEFAULT_LIMIT=25
export LITERATURE_SOURCES="arxiv,semanticscholar"

# Unpaywall (open access PDFs)
export LITERATURE_USE_UNPAYWALL=true
export UNPAYWALL_EMAIL=your@email.com

# LLM settings
export LLM_MODEL=llama3.2:3b
export LLM_TIMEOUT=600
```

See `infrastructure/literature/core/config.py` for complete configuration options.

## Documentation

- **[AGENTS.md](AGENTS.md)** - Complete system documentation
- **[infrastructure/literature/AGENTS.md](infrastructure/literature/AGENTS.md)** - Module documentation
- **[infrastructure/literature/README.md](infrastructure/literature/README.md)** - CLI reference

## License

Apache License 2.0

