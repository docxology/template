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
├── paper_selection.yaml  # NEW: Paper selection configuration
├── pdfs/                 # Downloaded PDFs (named by citation key)
│   ├── smith2024machine.pdf
│   └── jones2023deep.pdf
├── summaries/            # AI-generated paper summaries
│   └── smith2024machine_summary.md
└── llm_outputs/          # NEW: Advanced LLM operation results
    ├── literature_reviews/
    ├── science_communication/
    ├── comparative_analysis/
    ├── research_gaps/
    └── citation_networks/
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
├── UnpaywallSource (api.py)     # Open access PDF resolution
├── LibraryIndex (library_index.py)
├── PDFHandler (pdf_handler.py)
└── ReferenceManager (reference_manager.py)

LiteratureWorkflow (workflow.py)     # NEW: Orchestrates multi-paper operations
├── LiteratureLLMOperations (llm_operations.py)  # NEW: Advanced LLM synthesis
└── ProgressTracker (progress.py)

PaperSelector (paper_selector.py)    # NEW: Configurable paper filtering
└── PaperSelectionConfig

LiteratureConfig (config.py)
└── from_env() - Load from environment variables

SearchResult (api.py)
└── Normalized result dataclass

UnpaywallResult (api.py)
└── OA status and PDF URL

DownloadResult (core.py)
└── Success/failure with reason

LibraryEntry (library_index.py)
└── Paper metadata dataclass

LLMOperationResult (llm_operations.py)  # NEW: LLM operation results
└── Synthesis output with metadata
```

### Module Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public API exports |
| `core.py` | Main `LiteratureSearch` class + `DownloadResult` |
| `api.py` | API clients for arXiv, Semantic Scholar, Unpaywall |
| `config.py` | Configuration dataclass + browser User-Agents |
| `library_index.py` | JSON library index manager with cleanup methods |
| `pdf_handler.py` | PDF downloading with retry logic and fallbacks |
| `reference_manager.py` | BibTeX generation |
| `cli.py` | Command-line interface |
| `paper_selector.py` | **NEW**: Configurable paper selection and filtering |
| `llm_operations.py` | **NEW**: Advanced LLM operations for multi-paper synthesis |
| `workflow.py` | Orchestrates multi-paper operations with progress tracking |
| `progress.py` | Progress tracking for long-running literature tasks |
| `summarizer.py` | AI-powered paper summarization with quality validation |

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

# NEW: Clean up library (remove papers without PDFs)
python3 scripts/07_literature_search.py --cleanup

# NEW: Advanced LLM operations
python3 scripts/07_literature_search.py --llm-operation review
python3 scripts/07_literature_search.py --llm-operation communication --paper-config my_selection.yaml
python3 scripts/07_literature_search.py --llm-operation compare
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

## Interactive Literature Management Script

The repository includes an interactive script for managing academic literature with multiple operations:

```bash
# Basic operations:
./run.sh --search                  # Search literature (add to bibliography)
./run.sh --download                # Download PDFs (for bibliography entries)
./run.sh --summarize               # Generate summaries (for papers with PDFs)

# Maintenance:
./run.sh --cleanup                 # Remove papers without PDFs from library

# Advanced LLM operations:
./run.sh --llm-operation review    # Generate literature review synthesis
./run.sh --llm-operation communication  # Create science communication narrative
./run.sh --llm-operation compare   # Comparative analysis across papers
./run.sh --llm-operation gaps      # Identify research gaps
./run.sh --llm-operation network   # Analyze citation networks

# Or directly:
python3 scripts/07_literature_search.py --search-only
python3 scripts/07_literature_search.py --download-only
python3 scripts/07_literature_search.py --summarize
python3 scripts/07_literature_search.py --cleanup
python3 scripts/07_literature_search.py --llm-operation review
```

**Operations:**

1. **Search Only (--search-only)**:
   - Prompts for comma-separated keywords
   - Searches arXiv and Semantic Scholar (union of results)
   - Adds papers to BibTeX library and JSON index
   - No PDF downloading or summarization

2. **Download Only (--download-only)**:
   - Analyzes existing bibliography entries
   - Downloads PDFs for entries without PDFs
   - Shows detailed download statistics and progress
   - Updates library index with PDF paths

3. **Summarize Only (--summarize)**:
   - Finds papers with PDFs but no summaries
   - Generates structured summaries using local Ollama LLM
   - **Automatically skips existing summaries** - checks for `{citation_key}_summary.md` files before generating
   - Shows detailed timing and word count statistics

4. **Cleanup (--cleanup)**:
   - Removes papers from library that don't have PDFs
   - Shows statistics before cleanup with confirmation
   - Permanently removes entries from both BibTeX and JSON index
   - Helps maintain a clean, usable library

5. **LLM Operations (--llm-operation)**:
   - **Literature Review**: Synthesizes themes across multiple papers
   - **Science Communication**: Creates accessible narratives for general audiences
   - **Comparative Analysis**: Compares methods, results, or approaches across papers
   - **Research Gaps**: Identifies unanswered questions and future research directions
   - **Citation Networks**: Analyzes relationships and connections between papers
   - Uses paper selection config (`literature/paper_selection.yaml`) to filter papers
   - Saves results to `literature/llm_outputs/`

**Skip Existing Summaries:**
The summarize operation automatically detects and skips summary generation for papers that already have summary files. This check happens:
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

### PaperSelector **NEW**

```python
class PaperSelector:
    def __init__(self, config: PaperSelectionConfig):
        """Initialize with selection criteria."""

    @classmethod
    def from_config(cls, config_path: Path) -> PaperSelector:
        """Create selector from YAML config file."""

    def select_papers(self, library_entries: List[LibraryEntry]) -> List[LibraryEntry]:
        """Filter papers based on configured criteria."""
```

### LiteratureLLMOperations **NEW**

```python
class LiteratureLLMOperations:
    def generate_literature_review(
        self,
        papers: List[LibraryEntry],
        focus: str = "general",
        max_papers: int = 10
    ) -> LLMOperationResult:
        """Generate literature review synthesis."""

    def generate_science_communication(
        self,
        papers: List[LibraryEntry],
        audience: str = "general_public"
    ) -> LLMOperationResult:
        """Create accessible science communication narrative."""

    def generate_comparative_analysis(
        self,
        papers: List[LibraryEntry],
        aspect: str = "methods"
    ) -> LLMOperationResult:
        """Compare methods/findings across papers."""

    def identify_research_gaps(
        self,
        papers: List[LibraryEntry],
        domain: str = "general"
    ) -> LLMOperationResult:
        """Identify research gaps and future directions."""

    def analyze_citation_network(
        self,
        papers: List[LibraryEntry]
    ) -> LLMOperationResult:
        """Analyze citation relationships between papers."""
```

### LLMOperationResult **NEW**

```python
@dataclass
class LLMOperationResult:
    operation_type: str           # "literature_review", "science_communication", etc.
    papers_used: int              # Number of papers analyzed
    citation_keys: List[str]      # Keys of papers used
    output_text: str              # Generated content
    generation_time: float        # Time taken in seconds
    tokens_estimated: int         # Estimated token count
    metadata: Dict[str, Any]      # Operation-specific metadata
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

### PDF Download Error Categories

The PDF download system categorizes failures for better diagnostics:

| Category | Description | Example |
|----------|-------------|---------|
| `access_denied` | HTTP 403 Forbidden | Paywall or geo-blocking |
| `not_found` | HTTP 404 Not Found | Paper removed or URL changed |
| `rate_limited` | HTTP 429 Too Many Requests | API rate limit exceeded |
| `timeout` | Request timeout | Slow network or server issues |
| `network_error` | Connection/Socket errors | DNS, SSL, or network problems |
| `server_error` | HTTP 5xx errors | Server-side issues |
| `html_response` | HTML received instead of PDF | Publisher landing page |
| `html_no_pdf_link` | HTML page with no PDF links | Malformed or missing content |
| `content_mismatch` | Content-Type doesn't match content | Server misconfiguration |
| `invalid_response` | Malformed or unexpected response | API changes or bugs |

## Advanced Features

### HTML-to-PDF URL Extraction

When a URL returns HTML instead of a PDF, the system parses the HTML content to find PDF download links.

**Supported Patterns:**
- Direct `<a href="*.pdf">` links
- Meta tags with PDF URLs
- JavaScript variables containing PDF URLs
- Publisher-specific patterns (Elsevier, Springer, IEEE, Wiley)

**Fallback Chain:**
1. Original URL
2. Transformed URLs (PMC, arXiv, bioRxiv patterns)
3. HTML parsing (extract PDF links from pages)
4. Unpaywall lookup
5. Cross-reference search

### Progress Logging

The system provides progress tracking:

**Download Progress:**
```
[1/5] Novel Machine Learning Approach
[1/5] ✓ Downloaded: smith2024novel.pdf (2.1MB) - 1.2s
[2/5] ✗ Failed (access_denied): 403 Forbidden - 5.1s

PDF DOWNLOAD SUMMARY
============================================================
  Papers processed: 5
  ✓ Successful: 4 (80.0%)
    • Existed: 1
    • Downloaded: 3
  ✗ Failed: 1
  Time: 12.5s
  Average per paper: 2.5s
  Data downloaded: 8.7MB
============================================================
```

**Summarization Progress:**
```
✓ smith2024novel (45KB) - 8.2s

SUMMARIZATION SUMMARY
============================================================
  Papers processed: 3
  ✓ Successful: 3 (100.0%)
  Skipped: 0
  ✗ Failed: 0
  Time: 24.7s
  Average per paper: 8.2s
  Total summaries: 3
  Data generated: 135KB
  Average size: 45KB
============================================================
```

**Logging Levels:**
- **INFO**: Progress updates, completion status, statistics
- **WARNING**: Recoverable errors
- **ERROR**: Failures
- **DEBUG**: Detailed diagnostics

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
| `test_html_parsing.py` | HTML parsing and PDF URL extraction |
| `test_logging.py` | Logging functionality |
| `test_library_index.py` | Library index functionality |
| `test_core.py` | Core functionality |
| `test_integration.py` | Integration workflows |
| `test_literature_cli.py` | CLI interface tests |

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure overview
- [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) - System architecture
