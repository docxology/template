# Literature Search and Management System - Complete Documentation

## Overview

This is a **standalone repository** for academic literature search, PDF management, reference tracking, and AI-powered paper summarization. The system provides a complete workflow from paper discovery to analysis and citation management.

## System Architecture

### Standalone Design

This repository is completely independent and self-contained:
- **No dependencies** on external template or manuscript systems
- **Duplicated shared infrastructure** (`infrastructure/core/`, `infrastructure/llm/`) for independence
- **Separate bibliography** (`data/references.bib`) from any manuscript system
- **Complete test suite** for all functionality

### Directory Structure

```
literature/
├── run_literature.sh              # Main orchestrator (interactive menu)
├── scripts/                        # Orchestrator scripts
│   ├── 07_literature_search.py    # Literature search orchestrator
│   └── bash_utils.sh               # Shared bash utilities
├── infrastructure/                 # Core modules
│   ├── __init__.py                 # Package exports
│   ├── core/                       # Foundation utilities (duplicated)
│   │   ├── logging_utils.py       # Logging system
│   │   ├── exceptions.py          # Exception hierarchy
│   │   ├── config_loader.py        # Configuration management
│   │   ├── progress.py             # Progress tracking
│   │   └── ...
│   ├── llm/                        # LLM integration (duplicated)
│   │   ├── core.py                 # LLM client
│   │   ├── templates.py            # Prompt templates
│   │   └── ...
│   └── literature/                 # Literature-specific modules
│       ├── core/                   # Core search functionality
│       ├── sources/                # API adapters (arXiv, Semantic Scholar, etc.)
│       ├── pdf/                    # PDF handling
│       ├── library/                 # Library management
│       ├── workflow/                # Workflow orchestration
│       ├── summarization/          # AI summarization
│       ├── meta_analysis/           # Meta-analysis tools
│       └── ...
├── tests/                          # Test suite
│   └── infrastructure/
│       ├── core/                   # Core tests (filtered)
│       ├── llm/                    # LLM tests (filtered)
│       └── literature/             # Literature-specific tests
├── data/                           # Data directory
│   ├── library.json                # Paper metadata index
│   ├── references.bib              # BibTeX bibliography
│   ├── pdfs/                       # Downloaded PDFs
│   ├── summaries/                  # AI-generated summaries
│   ├── extracted_text/             # Extracted PDF text
│   └── output/                     # Meta-analysis outputs
└── docs/                           # Documentation
```

## Core Components

### Literature Search (`infrastructure/literature/core/`)

Main entry point for literature search functionality:

```python
from infrastructure.literature import LiteratureSearch, LiteratureConfig

config = LiteratureConfig.from_env()
searcher = LiteratureSearch(config)

# Search across multiple sources
papers = searcher.search("machine learning", limit=10)

# Add to library and download PDFs
for paper in papers:
    citation_key = searcher.add_to_library(paper)
    if paper.pdf_url:
        searcher.download_paper(paper)
```

**Features:**
- Multi-source search (arXiv, Semantic Scholar, PubMed, CrossRef, etc.)
- Automatic deduplication
- PDF download with open access fallback
- BibTeX generation
- Library indexing

### Library Management (`infrastructure/literature/library/`)

JSON-based library index tracking all papers:

**File:** `data/library.json`

```json
{
  "version": "1.0",
  "updated": "2025-12-02T04:42:16.615302",
  "count": 499,
  "entries": {
    "smith2024machine": {
      "citation_key": "smith2024machine",
      "title": "Machine Learning Advances in 2024",
      "authors": ["Dr. Jane Smith", "Dr. John Doe"],
      "year": 2024,
      "doi": "10.1234/example.doi",
      "source": "arxiv",
      "url": "http://arxiv.org/abs/2401.00001",
      "pdf_path": "data/pdfs/smith2024machine.pdf",
      "added_date": "2025-12-01T10:00:00.000000",
      "abstract": "This paper presents...",
      "venue": "arXiv preprint",
      "citation_count": 42
    }
  }
}
```

### Bibliography (`data/references.bib`)

Standard BibTeX format bibliography automatically generated from the library:

```bibtex
@article{smith2024machine,
  title={Machine Learning Advances in 2024},
  author={Smith, Jane and Doe, John},
  journal={arXiv preprint},
  year={2024},
  doi={10.1234/example.doi},
  url={http://arxiv.org/abs/2401.00001}
}
```

**Note:** This bibliography is **separate** from any manuscript system. It is maintained independently in this repository.

### PDF Management (`infrastructure/literature/pdf/`)

PDF downloading and text extraction:

- **Download**: Automatic PDF retrieval with retry logic
- **Naming**: PDFs named by citation key (e.g., `smith2024machine.pdf`)
- **Fallback**: Unpaywall open access resolution
- **Extraction**: Text extraction for summarization

### AI Summarization (`infrastructure/literature/summarization/`)

Local LLM-powered paper summarization:

**Requirements:**
- Ollama server running (`ollama serve`)
- Model installed (e.g., `ollama pull llama3.2:3b`)

**Usage:**
```bash
python3 scripts/07_literature_search.py --summarize
```

**Output:** Markdown summaries in `data/summaries/{citation_key}_summary.md`

### Meta-Analysis (`infrastructure/literature/meta_analysis/`)

Analysis tools for paper collections:

- **PCA Analysis**: Principal component analysis of paper metadata
- **Keyword Evolution**: Temporal keyword trends
- **Author Contributions**: Author network analysis
- **Visualizations**: Publication trends, keyword frequency, etc.

**Usage:**
```bash
python3 scripts/07_literature_search.py --meta-analysis --keywords "optimization"
```

## Workflow Operations

### Full Pipeline

```bash
./run_literature.sh
# Select option 0: Full Pipeline (search → download → extract → summarize)
```

### Individual Operations

```bash
# Search only (add to bibliography)
python3 scripts/07_literature_search.py --search-only --keywords "machine learning"

# Download PDFs
python3 scripts/07_literature_search.py --download-only

# Extract text from PDFs
python3 scripts/07_literature_search.py --extract-text

# Generate summaries
python3 scripts/07_literature_search.py --summarize

# Meta-analysis
python3 scripts/07_literature_search.py --meta-analysis --keywords "AI"
```

## Configuration

### Environment Variables

```bash
# Search settings
export LITERATURE_DEFAULT_LIMIT=25
export LITERATURE_SOURCES="arxiv,semanticscholar,pubmed"
export LITERATURE_MAX_RESULTS=100

# Unpaywall (open access PDFs)
export LITERATURE_USE_UNPAYWALL=true
export UNPAYWALL_EMAIL=your@email.com

# LLM settings
export LLM_MODEL=llama3.2:3b
export LLM_TIMEOUT=600
export MAX_PARALLEL_SUMMARIES=1

# Logging
export LOG_LEVEL=1  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR
```

### Configuration File

Create `.env` file in repository root:

```env
LITERATURE_DEFAULT_LIMIT=25
LITERATURE_SOURCES=arxiv,semanticscholar
LITERATURE_USE_UNPAYWALL=true
UNPAYWALL_EMAIL=your@email.com
LLM_MODEL=llama3.2:3b
```

## Testing

### Run Tests

```bash
# All tests
pytest

# Literature-specific tests
pytest tests/infrastructure/literature/

# Core infrastructure tests
pytest tests/infrastructure/core/

# LLM tests (requires Ollama)
pytest tests/infrastructure/llm/ -m requires_ollama

# Skip Ollama tests
pytest -m "not requires_ollama"
```

### Coverage

```bash
# Generate coverage report
pytest --cov=infrastructure --cov-report=html

# View report
open htmlcov/index.html
```

## CLI Usage

### Literature CLI

```bash
# Search
python3 -m infrastructure.literature.cli search "machine learning" --limit 10

# Library management
python3 -m infrastructure.literature.cli library stats
python3 -m infrastructure.literature.cli library list
python3 -m infrastructure.literature.cli library export --output export.json

# Cleanup
python3 -m infrastructure.literature.cli library cleanup --no-pdf
```

## Data Management

### Backup

```bash
# Complete backup
tar -czf literature_backup_$(date +%Y%m%d).tar.gz data/

# Metadata only
cp data/library.json data/references.bib backup/
```

### Maintenance

```bash
# Remove papers without PDFs
python3 scripts/07_literature_search.py --cleanup

# Validate library
python3 -m infrastructure.literature.cli library validate
```

## Integration Notes

### Standalone Operation

This repository is designed to operate **completely independently**:

- **No manuscript dependencies**: Bibliography is separate and independent
- **Self-contained infrastructure**: All required modules duplicated
- **Independent testing**: Complete test suite included
- **Standalone documentation**: All docs reflect standalone structure

### Bibliography Separation

The bibliography file (`data/references.bib`) is **separate** from any manuscript system:
- Maintained independently in this repository
- Can be manually copied to manuscript systems if needed
- No automatic synchronization with external systems

## Troubleshooting

### PDF Download Failures

```bash
# Check failed downloads
cat data/failed_downloads.json

# Retry downloads
python3 scripts/07_literature_search.py --download-only
```

### LLM Issues

```bash
# Check Ollama status
ollama ps

# Test model
ollama run llama3.2:3b "Hello"

# Install model
ollama pull llama3.2:3b
```

### Library Corruption

```bash
# Backup
cp data/library.json data/library.json.backup

# Validate
python3 -m infrastructure.literature.cli library validate
```

## See Also

- [infrastructure/literature/AGENTS.md](infrastructure/literature/AGENTS.md) - Module documentation
- [infrastructure/literature/README.md](infrastructure/literature/README.md) - CLI reference
- [infrastructure/core/AGENTS.md](infrastructure/core/AGENTS.md) - Core utilities
- [infrastructure/llm/AGENTS.md](infrastructure/llm/AGENTS.md) - LLM integration

