# Literature Search Module

## Purpose

The Literature Search module provides a unified interface for discovering scientific papers, managing references, and downloading full-text PDFs. It abstracts away the complexity of interacting with multiple academic databases (arXiv, Semantic Scholar, Unpaywall) and handling different response formats.

## Output Files

All literature outputs are saved to the `literature/` directory:

```
literature/
├── references.bib        # BibTeX entries for citations
├── library.json          # JSON index with full metadata
├── failed_downloads.json # Failed downloads for retry (if any)
└── pdfs/                 # Downloaded PDFs (named by citation key)
    ├── smith2024machine.pdf
    └── jones2023deep.pdf
```

## Architecture

This module follows the **thin orchestrator pattern**:
- **Core Logic**: Centralized in `core.py`, coordinating sources and handlers.
- **Adapters**: `api.py` contains adapters for each external API.
- **Handlers**: Specialized handlers for PDFs and references.
- **Library Index**: JSON-based tracking of all papers in `library_index.py`.
- **Configuration**: Centralized configuration management with environment variable support.
- **CLI**: Command-line interface for interactive use.

### Class Structure

```
LiteratureSearch (core.py)
├── ArxivSource (api.py)
├── SemanticScholarSource (api.py)
├── UnpaywallSource (api.py)     # NEW: Open access PDF resolution
├── LibraryIndex (library_index.py)
├── PDFHandler (pdf_handler.py)
└── ReferenceManager (reference_manager.py)

LiteratureConfig (config.py)
└── from_env() - Load from environment variables

SearchResult (api.py)
└── Normalized result dataclass

UnpaywallResult (api.py)         # NEW: Unpaywall lookup result
└── OA status and PDF URL

DownloadResult (core.py)         # NEW: Download tracking
└── Success/failure with reason

LibraryEntry (library_index.py)
└── Paper metadata dataclass
```

### Module Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public API exports |
| `core.py` | Main `LiteratureSearch` class + `DownloadResult` |
| `api.py` | API clients for arXiv, Semantic Scholar, Unpaywall |
| `config.py` | Configuration dataclass + browser User-Agents |
| `library_index.py` | JSON library index manager |
| `pdf_handler.py` | PDF downloading with retry logic and fallbacks |
| `reference_manager.py` | BibTeX generation |
| `cli.py` | Command-line interface |

## Usage

### Basic Search

```python
from infrastructure.literature import LiteratureSearch

lit = LiteratureSearch()
results = lit.search("large language models", limit=5)

for paper in results:
    print(f"{paper.title} ({paper.year})")
```

### Download and Cite

```python
# Download PDF (saved as citation_key.pdf)
pdf_path = lit.download_paper(results[0])

# Add to library (both BibTeX and JSON index)
citation_key = lit.add_to_library(results[0])
```

### Library Management

```python
# Get library statistics
stats = lit.get_library_stats()
print(f"Total papers: {stats['total_entries']}")
print(f"Downloaded PDFs: {stats['downloaded_pdfs']}")

# Get all library entries
entries = lit.get_library_entries()

# Export library to JSON
lit.export_library(Path("export.json"))
```

### Using Configuration

```python
from infrastructure.literature import LiteratureSearch, LiteratureConfig

# Custom configuration
config = LiteratureConfig(
    download_dir="/path/to/pdfs",
    bibtex_file="/path/to/references.bib",
    library_index_file="/path/to/library.json",
    timeout=60
)
lit = LiteratureSearch(config)

# Or load from environment
config = LiteratureConfig.from_env()
lit = LiteratureSearch(config)
```

### CLI Usage

```bash
# Search for papers (adds to library automatically)
python3 -m infrastructure.literature.cli search "machine learning" --limit 10

# Search and download PDFs
python3 -m infrastructure.literature.cli search "neural networks" --download

# Search specific sources
python3 -m infrastructure.literature.cli search "transformers" --sources arxiv,semanticscholar

# List papers in library
python3 -m infrastructure.literature.cli library list

# Show library statistics
python3 -m infrastructure.literature.cli library stats

# Export library to JSON
python3 -m infrastructure.literature.cli library export --output export.json
```

## Configuration

### Programmatic Configuration

```python
from infrastructure.literature import LiteratureConfig

config = LiteratureConfig(
    default_limit=25,           # Results per source per search
    max_results=100,            # Maximum total results
    arxiv_delay=3.0,            # Seconds between arXiv requests
    semanticscholar_delay=1.5,  # Seconds between Semantic Scholar requests
    semanticscholar_api_key="your-key",  # Optional API key
    retry_attempts=3,           # Retry failed requests
    retry_delay=5.0,            # Base delay for exponential backoff
    download_dir="literature/pdfs",
    bibtex_file="literature/references.bib",
    library_index_file="literature/library.json",
    timeout=0.1,
    sources=["arxiv", "semanticscholar"]
)
```

### Environment Variables

Load configuration from environment with `LiteratureConfig.from_env()`:

| Variable | Description | Default |
|----------|-------------|---------|
| `LITERATURE_DEFAULT_LIMIT` | Results per source per search | 25 |
| `LITERATURE_MAX_RESULTS` | Maximum total results | 100 |
| `LITERATURE_USER_AGENT` | User agent string | Research-Template-Bot/1.0 |
| `LITERATURE_ARXIV_DELAY` | Seconds between arXiv requests | 3.0 |
| `LITERATURE_SEMANTICSCHOLAR_DELAY` | Seconds between Semantic Scholar requests | 1.5 |
| `SEMANTICSCHOLAR_API_KEY` | Semantic Scholar API key | None |
| `LITERATURE_RETRY_ATTEMPTS` | Retry attempts for failed requests | 3 |
| `LITERATURE_RETRY_DELAY` | Base delay for exponential backoff | 5.0 |
| `LITERATURE_DOWNLOAD_DIR` | PDF download directory | literature/pdfs |
| `LITERATURE_TIMEOUT` | Request timeout (seconds) | 0.1 |
| `LITERATURE_BIBTEX_FILE` | BibTeX file path | literature/references.bib |
| `LITERATURE_LIBRARY_INDEX` | JSON index file path | literature/library.json |
| `LITERATURE_SOURCES` | Comma-separated sources | arxiv,semanticscholar |
| `LITERATURE_USE_UNPAYWALL` | Enable Unpaywall fallback (true/false) | false |
| `UNPAYWALL_EMAIL` | Email for Unpaywall API (required if enabled) | "" |
| `LITERATURE_DOWNLOAD_RETRY_ATTEMPTS` | Retry attempts for PDF downloads | 2 |
| `LITERATURE_DOWNLOAD_RETRY_DELAY` | Base delay for download retry (seconds) | 2.0 |
| `LITERATURE_USE_BROWSER_USER_AGENT` | Use browser User-Agent for downloads | true |

## Sources

### arXiv
- **API**: Public API (http://export.arxiv.org/api/query)
- **Rate Limit**: 3 seconds between requests (handled automatically)
- **Features**: Full text links, primary categories, DOI extraction

### Semantic Scholar
- **API**: Graph API (https://api.semanticscholar.org/graph/v1)
- **Auth**: Optional API key for higher rate limits
- **Rate Limit**: 1.5 seconds between requests with exponential backoff retry

### Unpaywall (Optional Fallback)
- **API**: Unpaywall API (https://api.unpaywall.org/v2)
- **Auth**: Requires email address (no API key needed)
- **Purpose**: Finds legal open access versions of paywalled papers
- **Usage**: Enable with `LITERATURE_USE_UNPAYWALL=true` and `UNPAYWALL_EMAIL=your@email.com`
- **Features**: Citation counts, open access PDF links, venue information
- **Retry Logic**: Automatic retry with exponential backoff on rate limit (429) errors

## Interactive Summarization Script

The repository includes an interactive script for searching, downloading, and summarizing papers using a local LLM:

```bash
./run.sh --search                  # Search literature and download PDFs
./run.sh --summarize               # Generate summaries for existing PDFs
# Or directly:
python3 scripts/07_literature_search.py --search
```

**Features:**
- Prompts for comma-separated keywords
- Searches both arXiv and Semantic Scholar (union of results)
- Downloads PDFs and adds to BibTeX library
- Generates structured summaries using local Ollama LLM
- **Automatically skips existing summaries** - checks for `{citation_key}_summary.md` files before generating
- Shows detailed timing and word count statistics
- Saves summaries to `literature/summaries/`

**Skip Existing Summaries:**
The workflow automatically detects and skips summary generation for papers that already have summary files. This check happens:
1. **File existence check** (primary) - Checks if `literature/summaries/{citation_key}_summary.md` exists
2. **Progress tracker check** (secondary) - Checks if progress tracker marks paper as "summarized"

If a summary file exists, the workflow:
- Skips expensive LLM summarization
- Returns a success result with the existing file path
- Updates progress tracker to mark as "summarized"
- Logs that the summary was skipped

This ensures idempotent runs - multiple executions with the same papers won't regenerate summaries unnecessarily.

**Output:**
```
literature/
├── pdfs/                    # Downloaded PDFs
├── summaries/               # LLM-generated summaries
│   └── {citation_key}_summary.md
├── library.json             # JSON index
└── references.bib           # BibTeX entries
```

## API Reference

### LiteratureSearch

```python
class LiteratureSearch:
    def __init__(self, config: Optional[LiteratureConfig] = None):
        """Initialize with optional configuration."""
    
    def search(
        self, 
        query: str, 
        limit: int = 10, 
        sources: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search for papers across enabled sources."""
    
    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result."""
    
    def add_to_library(self, result: SearchResult) -> str:
        """Add paper to both BibTeX and JSON library, returns citation key."""
    
    def export_library(self, path: Optional[Path] = None, format: str = "json") -> Path:
        """Export library to JSON file."""
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
    
    def get_library_entries(self) -> List[Dict[str, Any]]:
        """Get all library entries as dictionaries."""
```

### SearchResult

```python
@dataclass
class SearchResult:
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: str
    url: str
    doi: Optional[str] = None
    source: str = "unknown"
    pdf_url: Optional[str] = None
    venue: Optional[str] = None
    citation_count: Optional[int] = None
```

### LibraryIndex

```python
class LibraryIndex:
    def add_entry(
        self,
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        doi: Optional[str] = None,
        **metadata
    ) -> str:
        """Add entry to library, returns citation key."""
    
    def get_entry(self, citation_key: str) -> Optional[LibraryEntry]:
        """Get entry by citation key."""
    
    def list_entries(self) -> List[LibraryEntry]:
        """Get all library entries."""
    
    def has_paper(self, doi: Optional[str] = None, title: Optional[str] = None) -> bool:
        """Check if paper exists in library."""
    
    def export_json(self, path: Optional[Path] = None) -> Path:
        """Export library to JSON file."""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
```

### LibraryEntry

```python
@dataclass
class LibraryEntry:
    citation_key: str       # Unique key (matches PDF filename and BibTeX)
    title: str
    authors: List[str]
    year: Optional[int]
    doi: Optional[str]
    source: str             # Source database
    url: str
    pdf_path: Optional[str] # Relative path if downloaded
    added_date: str         # ISO format
    abstract: str
    venue: Optional[str]
    citation_count: Optional[int]
    metadata: Dict[str, Any]
```

### PDFHandler

```python
class PDFHandler:
    def download_pdf(
        self, 
        url: str, 
        filename: Optional[str] = None,
        result: Optional[SearchResult] = None
    ) -> Path:
        """Download PDF from URL using citation key as filename."""
    
    def download_paper(self, result: SearchResult) -> Optional[Path]:
        """Download PDF for a search result."""
    
    def extract_citations(self, pdf_path: Path) -> List[str]:
        """Extract citations from PDF (placeholder)."""
```

### ReferenceManager

```python
class ReferenceManager:
    def add_reference(self, result: SearchResult) -> str:
        """Add paper to BibTeX file, returns citation key."""
    
    def export_library(self, path: Optional[Path] = None) -> Path:
        """Export library to JSON via LibraryIndex."""
```

## Error Handling

The module uses custom exceptions from `infrastructure.core.exceptions`:

```python
from infrastructure.core.exceptions import (
    LiteratureSearchError,  # Search/API errors
    APIRateLimitError,      # Rate limit exceeded
    FileOperationError      # File I/O errors
)
```

Example:

```python
try:
    results = lit.search("query")
except LiteratureSearchError as e:
    print(f"Search failed: {e}")
    print(f"Context: {e.context}")
```

## Testing

Run tests with:

```bash
# All literature tests
pytest tests/infrastructure/literature/ -v

# With coverage
pytest tests/infrastructure/literature/ --cov=infrastructure/literature
```

### Test Organization

| File | Description |
|------|-------------|
| `test_config.py` | Configuration and environment loading |
| `test_pure_logic.py` | Pure logic tests (no network) |
| `test_api.py` | API client tests (mocked network) |
| `test_pdf_handler_comprehensive.py` | PDF handling tests |
| `test_library_index.py` | Library index functionality |
| `test_core.py` | Core functionality |
| `test_integration.py` | Integration workflows |
| `test_literature_cli.py` | CLI interface tests |

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure overview
- [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) - System architecture
