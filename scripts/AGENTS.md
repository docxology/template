# scripts/ - Generic Entry Point Orchestrators

## Purpose

Root-level `scripts/` directory contains **generic entry point orchestrators** that coordinate the template's build pipeline. These are reusable across any project.

Scripts in this directory:
- Discover and invoke project-specific scripts
- Coordinate build stages (setup, test, analysis, pdf, validate)
- Handle template-level orchestration
- Work with ANY project structure

**Project-specific analysis scripts belong in `project/scripts/`**, not here.

## Architectural Role

Root scripts are **thin orchestrators** that:
- Do NOT implement analysis or algorithms
- Discover and invoke `project/scripts/*.py`
- Handle I/O and orchestration
- Coordinate between stages
- Are generic across projects

## Entry Points

### 1. Setup Environment (`00_setup_environment.py`)

**Purpose:** Verify environment is ready

- Checks Python version
- Verifies dependencies
- Confirms build tools (pandoc, xelatex)
- Validates directory structure

**Generic:** Works for any project

### 2. Run Tests (`01_run_tests.py`)

**Purpose:** Execute complete test suite with enhanced reporting

- Runs infrastructure tests (`tests/infrastructure/`) with 49% coverage threshold
- Runs project tests (`project/tests/`) with 70% coverage threshold
- Supports quiet mode (`--quiet` or `-q`) - suppresses individual test names (default)
- Supports verbose mode (`--verbose` or `-v`) - shows all test names
- Generates HTML coverage reports for both suites
- Generates structured test reports (JSON, Markdown) to `project/output/reports/test_results.{json,md}`
- Reports individual and combined results with detailed metrics
- Generic orchestrator - does not implement tests

**Usage:**
```bash
# Quiet mode (default) - shows only summary
python3 scripts/01_run_tests.py

# Verbose mode - shows all test names
python3 scripts/01_run_tests.py --verbose
```

**Generic:** Works for any project using pytest

### 3. Run Analysis (`02_run_analysis.py`)

**Purpose:** Execute project analysis scripts with enhanced progress tracking

- Discovers scripts in `project/scripts/`
- Executes each script in order with progress tracking
- Uses `SubStageProgress` with EMA-based ETA for accurate time estimates
- Logs resource usage at start and end of stage
- Validates output generation
- Collects outputs to `project/output/`

**Progress Features:**
- Real-time progress updates with ETA
- Resource monitoring (memory, CPU)
- Per-script duration tracking

**Generic:** Works for any project with analysis scripts

### 4. Render PDF (`03_render_pdf.py`)

**Purpose:** Generate manuscript PDFs with progress tracking

- Processes `project/manuscript/` markdown files
- Uses `SubStageProgress` for multi-file rendering operations
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Logs resource usage during rendering
- Generic orchestrator

**Progress Features:**
- Progress bar for multiple file rendering
- Per-file completion tracking
- Resource usage monitoring

**Generic:** Works for any markdown manuscript

### 5. Validate Output (`04_validate_output.py`)

**Purpose:** Validate build quality with enhanced reporting

- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates enhanced validation reports (JSON, Markdown) with actionable recommendations
- Reports include priority levels, issue categorization, and specific fixes
- Reports saved to `project/output/reports/validation_report.{json,md}`
- Generic validation

**Generic:** Works for any project output

### 6. Copy Outputs (`05_copy_outputs.py`)

**Purpose:** Copy final deliverables to top-level output directory

- Cleans top-level `output/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF format)
- Copies all web outputs (HTML format)
- Validates all files copied successfully

**Generic:** Works for any project with rendered outputs

### 7. LLM Manuscript Review (`06_llm_review.py`)

**Purpose:** Generate AI-powered manuscript reviews using local Ollama LLM

- Checks Ollama availability and selects best model
- Extracts full text from combined PDF manuscript
- Generates executive summary, quality review, methodology review, and improvement suggestions
- Generates translations (if configured) - technical abstract in multiple languages
- Uses improved progress indicators:
  - Spinner during model loading
  - Streaming progress bar for review generation
  - Real-time token generation display with ETA
- Saves all reviews with detailed metrics to `project/output/llm/` (copied to `output/llm/` during copy stage)
- Tracks input/output sizes, token estimates, and generation times

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Maximum characters to send to LLM. Set to `0` for unlimited. |
| `LLM_LONG_MAX_TOKENS` | `4096` | Maximum tokens per review response. Configured via `LLMConfig.long_max_tokens`. Priority: env var > config default. |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout for each review generation (seconds). |

**Output Files:**
- `executive_summary.md` - Key findings and contributions
- `quality_review.md` - Writing clarity and style assessment
- `methodology_review.md` - Structure and methods evaluation
- `improvement_suggestions.md` - Actionable recommendations
- `translation_zh.md` - Technical abstract in Chinese (if configured)
- `translation_hi.md` - Technical abstract in Hindi (if configured)
- `translation_ru.md` - Technical abstract in Russian (if configured)
- `combined_review.md` - All reviews with generation metrics
- `review_metadata.json` - Model, config, and detailed metrics

**Metrics Tracked:**
- Manuscript input: characters, words, estimated tokens
- Per-review output: characters, words, tokens, generation time
- Truncation status (if any)
- Total generation time

**Optional:** Requires Ollama to be running with at least one model installed. Skips gracefully if unavailable.

**Model-Specific Behavior:**
The LLM review automatically adjusts for different model sizes:
- Small models (3B-8B): Flexible validation, higher temperature (+0.1)
- Large models (14B+): Standard validation thresholds

**Validation Approach:**

Uses structure-only validation for general-purpose use:
- Off-topic detection (critical - triggers retry with context reset)
- Word count requirements (structural)
- Header detection (flexible - accepts semantic equivalents)
- Emojis and tables are allowed

**Word Count Thresholds:**

| Review Type | Minimum Words | Template Target | Notes |
|------------|---------------|-----------------|-------|
| executive_summary | 250 | 400-600 | Full manuscript overview |
| quality_review | 300 | 500-700 | Detailed quality assessment |
| methodology_review | 300 | 500-700 | Methods and structure analysis |
| improvement_suggestions | 200 | 500-800 | Focused actionable items |
| translation | 400 | 200-400 (English) + translation | Technical abstract + target language |

Small models (3B-8B parameters) automatically receive 20% lower thresholds.

**Troubleshooting:**

| Issue | Cause | Solution |
|-------|-------|----------|
| "Response appears off-topic" | Model hallucinating | Auto-retries with context reset + reinforced prompt |
| "Missing expected structure" | Model used different headers | Validation accepts semantic equivalents |
| "Missing scoring rubric" | Score not in expected format | Validation accepts X/5, Rating: X, etc. |
| Response too short | Model stopped early | Retry with increased temperature |
| Generic book language | Model ignoring manuscript | Off-topic detection triggers retry |

**Translation Configuration:**

Translations are configured in `project/manuscript/config.yaml`:

```yaml
llm:
  translations:
    enabled: true  # Set to false to disable
    languages:
      - zh  # Chinese (Simplified)
      - hi  # Hindi
      - ru  # Russian
```

When enabled, the system generates a technical abstract (~200-400 words) in English, then translates it to each configured language. Each translation is saved as a separate file (e.g., `translation_zh.md`) and included in the combined review.

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Maximum chars to send. `0` = unlimited |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout per review in seconds |
| `LOG_LEVEL` | `1` | Set to `0` for validation debug info |

**Generic:** Works for any project with a combined PDF manuscript

### 8. Literature Operations (`07_literature_search.py`)

**Purpose:** Manage academic literature with separate operations

- **Search-only**: Searches arXiv and Semantic Scholar APIs, adds papers to bibliography (network only, no Ollama required)
- **Download-only**: Downloads PDFs for existing bibliography entries via HTTP (network only, no Ollama required)
- **Summarize-only**: Generates AI summaries for papers with PDFs (requires Ollama)
- **Cleanup**: Removes papers without PDFs from library (local files only, no Ollama required)
- **LLM Operations**: Advanced LLM operations like literature review synthesis (requires Ollama)

**Usage:**
```bash
# Search and add to bibliography only
python3 scripts/07_literature_search.py --search-only
python3 scripts/07_literature_search.py --search-only --keywords "machine learning,optimization"
python3 scripts/07_literature_search.py --search-only --limit 50 --keywords "AI"

# Download PDFs for bibliography entries
python3 scripts/07_literature_search.py --download-only

# Generate summaries for papers with PDFs
python3 scripts/07_literature_search.py --summarize

# All operations in sequence
python3 scripts/07_literature_search.py --search --summarize
```

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `LITERATURE_DEFAULT_LIMIT` | `25` | Results per source per keyword |
| `MAX_PARALLEL_SUMMARIES` | `1` | Parallel summarization workers |
| `LLM_SUMMARIZATION_TIMEOUT` | `600` | Timeout for paper summarization (seconds) |

**Output Files:**
- `literature/references.bib` - BibTeX entries
- `literature/library.json` - JSON index of all papers
- `literature/pdfs/` - Downloaded PDF files
- `literature/summaries/` - AI-generated summaries (markdown)
- `literature/summarization_progress.json` - Progress tracking

**Dependencies:**
- **Search/Download/Cleanup**: Network access only (no Ollama required)
- **Summarize/LLM Operations**: Requires Ollama server running with at least one model installed

**Generic:** Works for any project needing literature management

### 9. Run All (`run_all.py`)

**Purpose:** Execute core pipeline (Python orchestrator) with comprehensive reporting

- Orchestrates 6 core stages sequentially (00-05)
- Stops on first failure
- Provides detailed summary report with performance metrics
- Generates consolidated pipeline report (JSON, HTML, Markdown) to `project/output/reports/`
- Includes test results, validation results, performance metrics, error summaries
- Tracks resource usage per stage (memory, CPU, disk I/O)
- Identifies performance bottlenecks automatically
- No LLM dependencies required
- Generic core pipeline (excludes optional LLM stages)

**Generated Reports:**
- `pipeline_report.{json,html,md}` - Complete pipeline execution summary
- Includes stage durations, status, test results, validation results
- HTML version provides visual dashboard

**Note:** For interactive use or LLM features, prefer `./run.sh`. This Python orchestrator provides the minimal core pipeline.

**Generic:** Works for any project

## Menu-to-Script Mapping

The interactive menu (`./run.sh`) maps to Python scripts as follows. Menu numbering aligns with script numbering (0-7 for core scripts including LLM review/translations, 8 for full pipeline, 9+ for literature operations):

| Menu Option | Script | Arguments | Requires Ollama | Description |
|-------------|--------|-----------|----------------|-------------|
| 0 | `00_setup_environment.py` | - | No | Setup Environment |
| 1 | `01_run_tests.py` | - | No | Run Tests (infrastructure + project) |
| 2 | `02_run_analysis.py` | - | No | Run Analysis |
| 3 | `03_render_pdf.py` | - | No | Render PDF (also runs `02_run_analysis.py`) |
| 4 | `04_validate_output.py` | - | No | Validate Output |
| 5 | `05_copy_outputs.py` | - | No | Copy Outputs |
| 6 | `06_llm_review.py` | `--reviews-only` | Yes | LLM Review (manuscript review) |
| 7 | `06_llm_review.py` | `--translations-only` | Yes | LLM Translations (technical abstract translations) |
| 8 | `run.sh --pipeline` | - | No* | Run Full Pipeline (10 stages: 0-9, *stages 8-9 require Ollama) |
| 9 | `07_literature_search.py` | `--search --summarize` | No* | Literature Search (all operations, *summarize requires Ollama) |
| 10 | `07_literature_search.py` | `--search-only` | No | Search only (network only) |
| 11 | `07_literature_search.py` | `--download-only` | No | Download only (network only) |
| 12 | `07_literature_search.py` | `--summarize` | Yes | Summarize (requires Ollama) |
| 13 | `07_literature_search.py` | `--cleanup` | No | Cleanup (local files only) |
| 14 | `07_literature_search.py` | `--llm-operation` | Yes | Advanced LLM operations (requires Ollama) |
| 15 | `exit` | - | No | Exit menu |

This mapping is also available programmatically via `scripts.MENU_SCRIPT_MAPPING`.

## Entry Points

The template provides **two pipeline orchestrators** with different scope and features:

### Primary Entry Point: Interactive Menu (`./run.sh`)

The **recommended entry point** is the interactive `run.sh` script:

```bash
# Full interactive menu (recommended)
./run.sh

# Core Build Operations
./run.sh --pipeline          # Extended pipeline (10 stages: 0-9, includes LLM)
./run.sh --infra-tests        # Run infrastructure tests only
./run.sh --project-tests      # Run project tests only
./run.sh --render-pdf         # Render PDF manuscript only

# LLM Operations (requires Ollama)
./run.sh --reviews            # LLM manuscript review only
./run.sh --translations       # LLM translations only

# Literature Operations:
./run.sh --search             # Search literature (network only, add to bibliography)
./run.sh --download           # Download PDFs (network only, for bibliography entries)
./run.sh --summarize          # Generate summaries (requires Ollama, for papers with PDFs)
./run.sh --cleanup            # Cleanup library (local files only, remove papers without PDFs)
```

### Shorthand sequences

You can run multiple menu options in one go by concatenating digits:

- `./run.sh --option 012345` runs options 0 → 1 → 2 → 3 → 4 → 5
- From the interactive prompt, entering `345` runs analysis → render PDF → validate
- Comma-separated forms like `3,4,5` also work
- Sequences stop on the first non-zero exit code

Note: each digit is treated as a separate option; enter two-digit menu numbers (10+) explicitly.

**Features:**
- 10-stage pipeline (stages 0-9) including optional LLM review stages (8-9)
- Interactive menu for easy selection
- Individual stage execution options
- Literature search and summarization capabilities

### Alternative Entry Point: Python Orchestrator (`run_all.py`)

For programmatic use, the Python orchestrator provides a 6-stage core pipeline:

```bash
# Core pipeline only (no LLM stages)
python3 scripts/run_all.py
```

**Features:**
- 6-stage pipeline (core build only)
- No LLM dependencies required
- Programmatic execution
- Suitable for automated environments

**Stage Numbering Differences:**
- `run.sh`: Stages 0-9 (10 total). Stage 0 is cleanup (not tracked), stages 1-9 are displayed as [1/9] to [9/9] in logs
- `run_all.py`: Stages 00-05 (zero-padded Python convention, 6 core stages)

See [`../RUN_GUIDE.md`](../RUN_GUIDE.md) for complete documentation.

## Project-Specific Scripts

Analysis scripts specific to a project belong in `project/scripts/`:

```
project/scripts/
├── analysis_pipeline.py     # Project-specific analysis
├── example_figure.py        # Project-specific figures
└── README.md                # Project script documentation
```

These scripts:
- Import from `project/src/` for scientific computation
- Import from `infrastructure/` for document management
- Use the **thin orchestrator pattern**
- Are discovered and executed by root `02_run_analysis.py`

**Example:**
```python
# project/scripts/analysis_pipeline.py
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats
from infrastructure.documentation.figure_manager import FigureManager

# Generate and analyze
data = generate_synthetic_data(n_samples=1000)
stats = calculate_descriptive_stats(data)

# Register output
fm = FigureManager()
fm.register_figure("results.png", label="fig:results")
```

## Pattern: Generic Orchestrator

### ✅ CORRECT Pattern (Root Entry Points)

Root entry points use **thin orchestrator pattern**:
- Import infrastructure modules, not business logic
- Coordinate between pipeline stages
- Delegate all computation to imported modules
- Work with ANY project following this structure

```python
# scripts/03_render_pdf.py - Generic orchestrator
from infrastructure.rendering import RenderManager
from infrastructure.rendering.manuscript_discovery import (
    discover_manuscript_files,
    verify_figures_exist,
)

def run_render_pipeline() -> int:
    """Orchestrate PDF rendering stage."""
    # Use infrastructure modules for business logic
    manuscript_dir = Path("project/manuscript")
    source_files = discover_manuscript_files(manuscript_dir)  # From infrastructure
    
    # Use infrastructure modules for rendering
    renderer = RenderManager()
    pdf = renderer.render_combined_pdf(source_files, manuscript_dir)
    
    return 0
```

**Key Points:**
- Uses `infrastructure.<module>` imports for ALL business logic
- Delegates ALL computation to infrastructure modules
- Coordinates pipeline stages only
- Works with ANY project
- NO business logic implemented in orchestrator

### ✅ CORRECT Pattern (Project Scripts)

```python
# project/scripts/analysis_pipeline.py - Project-specific orchestrator
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats

# Import from project/src/ for computation
data = generate_synthetic_data()
stats = calculate_descriptive_stats(data)

# Import from infrastructure/ for document management
from infrastructure.documentation.figure_manager import FigureManager
fm = FigureManager()
fm.register_figure("results.png")
```

**Key Points:**
- Imports from `project/src/` (computation)
- Imports from `infrastructure/` (utilities)
- Orchestrates workflow
- Handles I/O and visualization

### ❌ INCORRECT Pattern (Violates Architecture)

```python
# scripts/analysis_pipeline.py - WRONG location
from scientific.data_generator import generate_synthetic_data

# ❌ Root scripts should NOT contain analysis
# ❌ Duplicates project/scripts/ logic
# ❌ Not generic across projects
```

## Progress Tracking and Resource Monitoring

### Enhanced Progress Tracking

All scripts now include comprehensive progress tracking with improved accuracy:

**Features:**
- **EMA-based ETA** - Exponential moving average for smoother time estimates
- **Confidence intervals** - Optimistic/pessimistic ETA ranges
- **Sub-stage progress** - Track progress within multi-step operations
- **LLM token tracking** - Real-time token generation progress with throughput
- **Resource monitoring** - Memory and CPU usage at stage boundaries

**Usage in Scripts:**
```python
from infrastructure.core.progress import SubStageProgress, LLMProgressTracker
from infrastructure.core.logging_utils import log_resource_usage

# Track sub-stages with EMA
progress = SubStageProgress(total=10, stage_name="Processing", use_ema=True)
for i, item in enumerate(items, 1):
    progress.start_substage(i, item.name)
    process(item)
    progress.complete_substage()

# Resource monitoring
log_resource_usage("Stage start", logger)
# ... stage execution ...
log_resource_usage("Stage end", logger)
```

### Error Messages with Recovery Actions

Error messages now include automatic recovery commands:

**Features:**
- **Context-aware suggestions** - Based on error type
- **Automatic command generation** - OS-specific installation commands
- **File path resolution** - Specific file and line number context
- **Quick-fix commands** - Copy-paste ready solutions

**Example:**
```python
from infrastructure.core.exceptions import FileNotFoundError

raise FileNotFoundError(
    "Manuscript file not found",
    context={"file": "manuscript.md", "searched_in": "/path/to/project"}
)
# Automatically generates:
# - Suggestions for fixing the issue
# - Commands like: ls -la manuscript.md, find . -name 'manuscript.md'
```

## Integration with Build Pipeline

Complete pipeline execution (interactive):

```bash
./run.sh              # Interactive menu
./run.sh --pipeline    # Full pipeline non-interactively
```

Or via Python:

```bash
python3 scripts/run_all.py
```

**Pipeline Stages:**
1. **00_setup_environment.py** - Environment ready?
2. **01_run_tests.py** - Tests pass?
3. **02_run_analysis.py** - Executes `project/scripts/*.py`
4. **03_render_pdf.py** - PDFs generated?
5. **04_validate_output.py** - Output valid?
6. **05_copy_outputs.py** - Final deliverables copied?
7. **06_llm_review.py** - LLM manuscript review generated? (optional)

**Standalone Operations (via menu or direct):**
8. **07_literature_search.py** - Literature search & summarization

Each stage is **generic** and works with any project structure.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Maximum characters to send to LLM (Stage 7). Set to `0` for unlimited. |
| `LOG_LEVEL` | `1` | Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR) |

## Testing

Root entry points are tested through:
- Integration with project code
- Successful pipeline execution
- Correct delegation to project scripts

No unit tests needed for orchestrators - they're thin wrappers.

## Best Practices

### Do's ✅
- Keep root scripts generic
- Discover project scripts dynamically
- Delegate to `project/scripts/`
- Handle I/O and orchestration
- Use clear logging

### Don'ts ❌
- Implement analysis in root scripts
- Hardcode paths to specific analyses
- Assume specific project structure
- Skip error handling
- Import from `project/src/` in root scripts

## File Organization

```
scripts/
├── 00_setup_environment.py     # Entry: Setup
├── 01_run_tests.py             # Entry: Test
├── 02_run_analysis.py          # Entry: Analysis (discovers project/scripts/)
├── 03_render_pdf.py            # Entry: PDF rendering
├── 04_validate_output.py       # Entry: Validation
├── 05_copy_outputs.py          # Entry: Copy deliverables
├── 06_llm_review.py            # Entry: LLM manuscript review (optional)
├── 07_literature_search.py     # Entry: Literature search & summarization
├── run_all.py                  # Entry: Complete pipeline (Python)
├── __init__.py                 # Package exports for testing
├── AGENTS.md                   # This file
└── README.md                   # Quick reference

../run.sh                       # Unified entry point (interactive menu)

project/scripts/
├── analysis_pipeline.py        # Project-specific analysis
├── example_figure.py           # Project-specific figures
├── AGENTS.md                   # Project script docs
└── README.md                   # Project quick reference
```

## Deployment

### Using with Template

```bash
cd /path/to/template
python3 scripts/run_all.py  # Executes project/scripts/
```

### Using with Different Project

1. Create new `project/` structure
2. Add your code to `project/src/`
3. Add your scripts to `project/scripts/`
4. Run root entry points - they auto-discover your code

Root entry points work with **ANY** project that follows this structure.

## See Also

- [`README.md`](README.md) - Quick reference
- [`project/scripts/AGENTS.md`](../project/scripts/AGENTS.md) - Project scripts
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern explanation
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation

## Key Takeaway

**Root scripts are generic entry points:**
- ✅ Work with ANY project
- ✅ Discover `project/scripts/`
- ✅ Coordinate build stages
- ❌ Never implement analysis
- ❌ Never duplicate logic

**Project scripts are specific to each research:**
- ✅ Implement domain-specific logic
- ✅ Import from `project/src/`
- ✅ Use infrastructure tools
- ❌ Never duplicate root orchestration
