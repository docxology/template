# Literature Search Module

## Purpose

The Literature Search module provides a unified interface for discovering scientific papers, managing references, and downloading full-text PDFs. It abstracts away the complexity of interacting with multiple academic databases (arXiv, Semantic Scholar, Unpaywall) and handling different response formats.

## Output Files

All literature outputs are saved to the `data/` directory:

```
data/
├── references.bib        # BibTeX entries for citations
├── library.json          # JSON index with full metadata
├── failed_downloads.json # Failed downloads for retry (if any)
├── paper_selection.yaml  # NEW: Paper selection configuration
├── pdfs/                 # Downloaded PDFs (named by citation key)
│   ├── smith2024machine.pdf
│   └── jones2023deep.pdf
├── summaries/            # AI-generated paper summaries
│   └── smith2024machine_summary.md
├── extracted_text/       # Extracted text from PDFs
├── output/               # Meta-analysis outputs and visualizations
│   ├── pca_2d.png
│   ├── keyword_evolution.png
│   └── meta_analysis_summary.json
└── llm_outputs/          # NEW: Advanced LLM operation results
    ├── literature_reviews/
    ├── science_communication/
    ├── comparative_analysis/
    ├── research_gaps/
    └── citation_networks/
```

## Architecture

This module follows the **thin orchestrator pattern** and is organized into logical subdirectories:

### Directory Structure

```
infrastructure/literature/
├── core/              # Core functionality (search, config, CLI)
├── pdf/               # PDF handling and processing
├── library/           # Library management and indexing
├── analysis/          # Paper analysis tools
├── workflow/          # Workflow orchestration
├── meta_analysis/     # Meta-analysis and visualization (NEW)
├── llm/               # LLM operations
├── reporting/         # Reporting and export
├── sources/           # API adapters for external databases
├── html_parsers/      # HTML parsing for PDF extraction
└── summarization/     # Summarization system
```

### Module Organization

- **Core Logic**: Centralized in `core/`, coordinating sources and handlers.
- **Adapters**: `sources/` directory contains modular API adapters for each external database.
- **Handlers**: Specialized handlers for PDFs in `pdf/`.
- **Library Management**: JSON-based tracking in `library/`.
- **Configuration**: Centralized in `core/config.py` with environment variable support.
- **CLI**: Command-line interface in `core/cli.py`.
- **Meta-Analysis**: Temporal, keyword, metadata, and PCA analysis in `meta_analysis/` (NEW).

### Class Structure

```
LiteratureSearch (core.py)
├── ArxivSource (sources/arxiv.py)
├── SemanticScholarSource (sources/semanticscholar.py)
├── UnpaywallSource (sources/unpaywall.py)     # Open access PDF resolution
├── BiorxivSource (sources/biorxiv.py)         # bioRxiv/medRxiv preprints
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

SearchResult (sources/base.py)
└── Normalized result dataclass

UnpaywallResult (sources/unpaywall.py)
└── OA status and PDF URL

DownloadResult (core.py)
└── Success/failure with reason

LibraryEntry (library_index.py)
└── Paper metadata dataclass

LLMOperationResult (llm_operations.py)  # NEW: LLM operation results
└── Synthesis output with metadata
```

### Module Files

| Directory/File | Purpose |
|----------------|---------|
| `__init__.py` | Public API exports |
| **core/** | Core functionality |
| `core/core.py` | Main `LiteratureSearch` class + `DownloadResult` |
| `core/config.py` | Configuration dataclass + browser User-Agents |
| `core/cli.py` | Command-line interface |
| **pdf/** | PDF handling |
| `pdf/handler.py` | PDF downloading with retry logic and fallbacks |
| `pdf/downloader.py` | PDF download implementation |
| `pdf/extractor.py` | Text extraction utilities |
| `pdf/fallbacks.py` | Fallback strategies for PDF URLs |
| **library/** | Library management |
| `library/index.py` | JSON library index manager |
| `library/stats.py` | Library statistics |
| `library/references.py` | BibTeX generation |
| `library/clear.py` | Library cleanup operations |
| **analysis/** | Paper analysis |
| `analysis/paper_analyzer.py` | Paper structure/content analysis |
| `analysis/domain_detector.py` | Domain detection |
| `analysis/context_builder.py` | Context building for LLM |
| **workflow/** | Workflow orchestration |
| `workflow/workflow.py` | Multi-paper operations orchestration |
| `workflow/orchestrator.py` | Search workflow orchestration |
| `workflow/progress.py` | Progress tracking |
| **meta_analysis/** | Meta-analysis and visualization (NEW) |
| `meta_analysis/aggregator.py` | Data aggregation for analysis |
| `meta_analysis/temporal.py` | Publication year analysis |
| `meta_analysis/keywords.py` | Keyword evolution analysis |
| `meta_analysis/metadata.py` | Metadata visualization |
| `meta_analysis/pca.py` | PCA analysis of texts |
| `meta_analysis/visualizations.py` | Plotting utilities |
| **llm/** | LLM operations |
| `llm/operations.py` | Advanced LLM operations for multi-paper synthesis |
| `llm/selector.py` | Configurable paper selection and filtering |
| **reporting/** | Reporting |
| `reporting/reporter.py` | Comprehensive reporting with export |
| **sources/** | API adapters |
| `sources/base.py` | Base classes (`SearchResult`, `LiteratureSource`) |
| `sources/arxiv.py` | arXiv API client |
| `sources/semanticscholar.py` | Semantic Scholar API client |
| `sources/unpaywall.py` | Unpaywall API client |
| `sources/biorxiv.py` | bioRxiv/medRxiv API client |
| **html_parsers/** | HTML parsing |
| `html_parsers/` | Publisher-specific HTML parsers |
| **summarization/** | Summarization system |
| `summarization/` | Modular summarization system (see below) |

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
    download_dir="data/pdfs",
    bibtex_file="data/references.bib",
    library_index_file="data/library.json",
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
| `LITERATURE_DOWNLOAD_DIR` | PDF download directory | data/pdfs |
| `LITERATURE_TIMEOUT` | Request timeout (seconds) | 0.1 |
| `LITERATURE_BIBTEX_FILE` | BibTeX file path | data/references.bib |
| `LITERATURE_LIBRARY_INDEX` | JSON index file path | data/library.json |
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

### Unpaywall (Optional Fallback - Lookup Only)
- **API**: Unpaywall API (https://api.unpaywall.org/v2)
- **Auth**: Requires email address (no API key needed)
- **Purpose**: Finds legal open access versions of paywalled papers
- **Usage**: Enable with `LITERATURE_USE_UNPAYWALL=true` and `UNPAYWALL_EMAIL=your@email.com`
- **Features**: Citation counts, open access PDF links, venue information
- **Retry Logic**: Automatic retry with exponential backoff on rate limit (429) errors
- **Special Status**: This is a **lookup-only source** - it does not support general search queries. It only provides DOI-based lookups for open access PDF resolution. It is automatically excluded from search operations but included in health status checks.
- **Health Monitoring**: 
  - `check_health()`: Performs a test DOI lookup to verify API availability
  - `is_healthy`: Property indicating health based on recent consecutive failures
  - `get_health_status()`: Returns detailed health status information matching the format used by other sources

## Source Capabilities and Health Status

### Source Types

Sources are categorized by their capabilities:

1. **Search Sources** (inherit from `LiteratureSource`):
   - Support general search queries via `search()` method
   - Examples: arXiv, Semantic Scholar, bioRxiv, PubMed, Europe PMC, CrossRef, OpenAlex, DBLP
   - All support health status methods: `check_health()`, `is_healthy`, `get_health_status()`

2. **Lookup-Only Sources** (do not inherit from `LiteratureSource`):
   - Only support specific lookups (e.g., DOI-based)
   - Example: Unpaywall (DOI-based open access PDF lookup)
   - Still support health status methods for monitoring
   - Automatically excluded from general search operations

### Health Status Methods

All sources (search and lookup-only) support health monitoring:

- **`check_health()`**: Performs an actual health check (e.g., test search/lookup)
  - Returns `True` if source is healthy, `False` otherwise
  - May make network requests
  
- **`is_healthy`** (property): Cached health status based on recent failures
  - Returns `True` if consecutive failures < 3, `False` otherwise
  - No network requests required
  
- **`get_health_status()`**: Returns detailed health status dictionary:
  ```python
  {
      "healthy": bool,
      "consecutive_failures": int,
      "last_request_time": float,
      "source_name": str
  }
  ```

### Health Status in LiteratureSearch

The `LiteratureSearch` class provides methods to check health across all sources:

- **`get_source_health_status()`**: Returns health status for all configured sources
  - Handles sources without health methods gracefully
  - Returns default status for unsupported sources
  
- **`check_all_sources_health()`**: Performs actual health checks for all sources
  - May take time as it makes network requests
  - Returns simple True/False mapping
  
- **`_ping_sources()`**: Internal method used before search operations
  - Checks availability of sources before attempting search
  - Automatically skips lookup-only sources from search operations

## PDF Download Optimization

The PDF download system implements several optimizations to reduce log verbosity and prevent excessive retry attempts:

### Recursion Depth Limiting
- **Maximum recursion depth**: 2 levels for HTML-to-PDF URL extraction
- **Prevents**: Infinite loops when HTML pages link to other HTML pages
- **Behavior**: Stops parsing HTML for PDF URLs after 2 levels of redirection

### Intelligent Logging
- **Debug-level warnings**: Intermediate retry failures logged at DEBUG level
- **Summary-only approach**: Only final failures logged at WARNING/ERROR level
- **Prevents flooding**: Hundreds of redundant warnings suppressed
- **What you'll see**:
  - DEBUG: Individual retry attempt failures (use `LOG_LEVEL=0` to see)
  - INFO: Successful downloads and progress updates
  - WARNING/ERROR: Final failure summaries only

### Retry Limits
- **HTML URL extraction**: Maximum 3 URLs tried at depth 0, 2 URLs at depth 1+
- **Transform strategies**: Limited to 3 URL transformations per paper
- **User-Agent rotation**: Limited to 3 different browser User-Agents
- **Total attempts**: Typically 10-20 URLs per paper vs. hundreds previously

### Download Summary Reporting
After all downloads complete, a comprehensive summary is displayed:
```
PDF DOWNLOAD SUMMARY
=====================================================================
  Total papers processed: 20
  ✓ Successfully downloaded: 7 (35.0%)
    • Already existed: 1
    • Newly downloaded: 6
  ✗ Failed downloads: 13
  ⏱️  Total time: 180.5s
  📊 Average time per paper: 9.0s
```

Failure breakdown by category:
```
Download failure breakdown:
  • html_response: 5
  • access_denied: 4
  • html_no_pdf_link: 3
  • not_found: 1
```

### Performance Impact
- **90% reduction**: In log output volume
- **Faster completion**: Less time spent on futile retry attempts
- **Better diagnostics**: Summary view shows overall success patterns
- **Cleaner output**: Terminal remains readable during long operations

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
1. **File existence check** (primary) - Checks if `data/summaries/{citation_key}_summary.md` exists
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

### SummarizationEngine

```python
class SummarizationEngine:
    def __init__(
        self,
        llm_client: LLMClient,
        quality_validator: Optional[SummaryQualityValidator] = None,
        context_extractor: Optional[ContextExtractor] = None,
        prompt_builder: Optional[SummarizationPromptBuilder] = None,
        max_pdf_chars: Optional[int] = None
    ):
        """Initialize summarization engine.
        
        Args:
            llm_client: Configured LLM client for summary generation.
            quality_validator: Quality validator instance (created if None).
            context_extractor: Context extractor instance (created if None).
            prompt_builder: Prompt builder instance (created if None).
            max_pdf_chars: Maximum PDF characters to send to LLM.
                          Defaults to 200000 (200K) or LLM_MAX_INPUT_LENGTH env var.
        """
    
    def summarize_paper(
        self,
        result: SearchResult,
        pdf_path: Path,
        max_retries: int = 2
    ) -> SummarizationResult:
        """Generate summary for a single paper with quality validation.
        
        Implements multi-stage summarization:
        1. PDF text extraction with section prioritization
        2. Structured context extraction
        3. Draft generation
        4. Quality validation
        5. Automatic refinement (if needed)
        
        Args:
            result: Search result with paper metadata.
            pdf_path: Path to PDF file.
            max_retries: Maximum retry attempts for generation.
        
        Returns:
            SummarizationResult with summary and metadata.
        """
    
    def save_summary(
        self,
        result: SearchResult,
        summary_result: SummarizationResult,
        output_dir: Path,
        pdf_path: Optional[Path] = None
    ) -> Path:
        """Save summary to markdown file and metadata to JSON.
        
        Args:
            result: Search result with paper metadata.
            summary_result: Summarization result to save.
            output_dir: Directory for summary files.
            pdf_path: Path to PDF file (for metadata).
        
        Returns:
            Path to saved summary file.
        
        Raises:
            FileOperationError: If saving fails.
        """
    
    @property
    def quality_validator(self) -> SummaryQualityValidator:
        """Property alias for validator (backward compatibility)."""
```

### SummaryQualityValidator

```python
class SummaryQualityValidator:
    def __init__(self, min_words: int = 200):
        """Initialize quality validator.
        
        Args:
            min_words: Minimum word count for valid summaries.
        """
    
    def validate_summary(
        self,
        summary: str,
        pdf_text: str,
        citation_key: str,
        paper_title: Optional[str] = None
    ) -> Tuple[bool, float, List[str]]:
        """Validate summary quality comprehensively.
        
        Performs multiple checks:
        - Title matching
        - Content topic matching
        - Quote/evidence presence
        - Length validation
        - Repetition detection (sentence, paragraph, section level)
        - Hallucination detection
        - Off-topic content detection
        
        Args:
            summary: Generated summary text.
            pdf_text: Original PDF text for comparison.
            citation_key: Citation key for logging.
            paper_title: Paper title for title matching validation.
        
        Returns:
            Tuple of (is_valid, quality_score, error_messages).
        """
    
    def validate_summary_detailed(
        self,
        summary: str,
        pdf_text: str,
        citation_key: str,
        paper_title: Optional[str] = None,
        key_terms: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate summary and return detailed ValidationResult.
        
        Args:
            summary: Generated summary text.
            pdf_text: Original PDF text for comparison.
            citation_key: Citation key for logging.
            paper_title: Paper title for validation.
            key_terms: Optional list of key terms that should be mentioned.
        
        Returns:
            ValidationResult with detailed validation information.
        """
```

### SummarizationResult

```python
@dataclass
class SummarizationResult:
    citation_key: str              # Unique identifier for the paper
    success: bool                  # Whether summarization succeeded
    summary_text: Optional[str]    # Generated summary text if successful
    input_chars: int               # Number of characters in extracted PDF text
    input_words: int               # Number of words in extracted PDF text
    output_words: int              # Number of words in generated summary
    generation_time: float         # Time taken for summarization in seconds
    attempts: int                  # Number of attempts made
    error: Optional[str]           # Error message if summarization failed
    quality_score: float           # Quality validation score (0.0 to 1.0)
    validation_errors: List[str]   # List of quality validation issues
    summary_path: Optional[Path]   # Path to the saved summary file if successful
    skipped: bool                  # Whether this summary was skipped (already exists)
    
    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio (output/input words)."""
    
    @property
    def words_per_second(self) -> float:
        """Calculate generation speed in words per second."""
```

### MultiStageSummarizer

```python
class MultiStageSummarizer:
    def __init__(
        self,
        llm_client: LLMClient,
        validator: SummaryQualityValidator,
        prompt_builder: SummarizationPromptBuilder,
        max_refinement_attempts: int = 2
    ):
        """Initialize multi-stage summarizer."""
    
    def summarize_with_refinement(
        self,
        context: SummarizationContext,
        pdf_text: str,
        metadata: dict,
        citation_key: str
    ) -> Tuple[str, ValidationResult, int]:
        """Generate summary with automatic refinement.
        
        Args:
            context: Structured context from paper.
            pdf_text: Full PDF text for validation.
            metadata: Paper metadata.
            citation_key: Citation key for logging.
        
        Returns:
            Tuple of (final_summary, final_validation_result, total_attempts).
        """
```

### ContextExtractor

```python
class ContextExtractor:
    def create_summarization_context(
        self,
        pdf_text: str,
        title: str,
        max_chars: Optional[int] = None
    ) -> SummarizationContext:
        """Create structured context object for summarization.
        
        Args:
            pdf_text: Full PDF text.
            title: Paper title.
            max_chars: Optional maximum characters for context.
        
        Returns:
            SummarizationContext with structured information.
        """
    
    def extract_paper_structure(self, pdf_text: str) -> PaperStructure:
        """Identify all sections in PDF text.
        
        Returns:
            PaperStructure with identified sections.
        """
    
    def extract_key_terms(self, pdf_text: str, title: str) -> List[str]:
        """Extract actual key terms from title and abstract.
        
        Returns:
            List of key terms (4+ characters, not stop words).
        """
```

### PDFProcessor

```python
class PDFProcessor:
    def extract_prioritized_text(
        self,
        pdf_path: Path,
        max_chars: int
    ) -> PrioritizedPDFText:
        """Extract and prioritize PDF text for summarization.
        
        Preserves critical sections (title, abstract, introduction, conclusion)
        when truncating long papers.
        
        Args:
            pdf_path: Path to PDF file.
            max_chars: Maximum characters to extract (0 for unlimited).
        
        Returns:
            PrioritizedPDFText with processed text and metadata.
        """
    
    def identify_sections(self, pdf_text: str) -> Dict[str, Tuple[int, int]]:
        """Identify key sections in PDF text.
        
        Returns:
            Dictionary mapping section names to (start_char, end_char) positions.
        """
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
[1/3] Processing smith2024novel...
[smith2024novel] Extracted 125,432 chars, 23,456 words from smith2024novel.pdf
[smith2024novel] Extracting structured context...
[smith2024novel] Context extracted in 0.15s: abstract=1,234 chars, intro=3,456 chars, conclusion=2,345 chars, key_terms=12
[smith2024novel] Starting multi-stage summarization...
[smith2024novel] Stage 1: Generating draft summary...
[smith2024novel] Draft generated in 12.3s: 8,234 chars, 1,234 words
[smith2024novel] Validating summary quality...
[smith2024novel] Summary accepted (score: 0.85, validation time: 0.45s, quotes: 5)
[smith2024novel] Summary accepted: 1,234 words, quality score: 0.85, compression ratio: 5.26%
[1/3] ✓ smith2024novel (45KB) - 13.1s, 1,234 words, quality: 0.85

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

### Summarization Architecture

The literature module uses a **modular, multi-stage summarization system** located in `summarization/`:

**Core Components:**
- **`SummarizationEngine`** (`core.py`) - Main orchestrator coordinating all stages
- **`MultiStageSummarizer`** (`multi_stage_summarizer.py`) - Draft generation and refinement workflow
- **`PDFProcessor`** (`pdf_processor.py`) - Intelligent PDF text extraction with section prioritization
- **`ContextExtractor`** (`context_extractor.py`) - Structured context extraction from PDFs
- **`PromptBuilder`** (`prompt_builder.py`) - LLM prompt construction with examples and validation checklists
- **`SummaryQualityValidator`** (`validator.py`) - Comprehensive quality validation and issue detection

**Summarization Pipeline:**
1. **PDF Text Extraction** - Prioritized extraction preserving title, abstract, introduction, conclusion
2. **Context Extraction** - Structured context with key terms, equations, and section identification
3. **Draft Generation** - Initial summary using domain-aware prompts
4. **Quality Validation** - Comprehensive validation checking title match, topics, repetition, hallucination
5. **Refinement** (if needed) - Automatic refinement addressing validation issues
6. **Final Validation** - Acceptance check with quality scoring

**Real-Time Logging:**
All stages provide real-time logging with citation key prefixes:
- `[citation_key]` - All log messages include paper identifier
- Stage-by-stage progress (extraction, context, generation, validation)
- Timing information for each stage
- Quality metrics (score, word count, compression ratio)
- Validation results (errors, warnings, suggestions)

**Progress Tracking:**
- Integrated with `ProgressTracker` for resumable operations
- Real-time status updates (pending → processing → summarized/failed)
- Progress bars for batch operations
- Structured logging with JSON format option

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

## Meta-Analysis Module

The `meta_analysis/` module provides comprehensive analysis and visualization tools for your literature library:

### Features

**Temporal Analysis** (`temporal.py`):
- Publication trends by year
- Publication rate analysis
- Year-based filtering

**Keyword Analysis** (`keywords.py`):
- Keyword frequency over time
- Emerging keyword detection
- Keyword evolution visualization

**Metadata Visualization** (`metadata.py`):
- Venue distribution
- Author contributions
- Citation distribution
- Source statistics

**PCA Analysis** (`pca.py`):
- Text feature extraction (TF-IDF)
- Principal component analysis
- Paper clustering
- 2D and 3D visualizations

### Usage Example

```python
from infrastructure.literature.meta_analysis import (
    DataAggregator,
    create_publication_timeline_plot,
    create_keyword_frequency_plot,
    create_pca_2d_plot,
)

# Create aggregator
aggregator = DataAggregator()

# Publication timeline
create_publication_timeline_plot()

# Keyword analysis
from infrastructure.literature.meta_analysis import extract_keywords_over_time
keyword_data = extract_keywords_over_time()
create_keyword_frequency_plot(keyword_data, top_n=20)

# PCA analysis
create_pca_2d_plot(n_clusters=5)
```

### Dependencies

The meta_analysis module requires:
- `matplotlib` for plotting
- `numpy` for numerical operations
- `scikit-learn` for PCA and clustering (optional, for PCA features)
- `pandas` for data manipulation (optional)

## See Also

- [`README.md`](README.md) - Quick reference
- [`meta_analysis/AGENTS.md`](meta_analysis/AGENTS.md) - Meta-analysis documentation
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure overview
- [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) - System architecture
