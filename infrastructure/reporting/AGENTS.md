# Reporting Module - Complete Documentation

## Overview

The reporting module provides comprehensive reporting capabilities for pipeline execution, test results, validation outcomes, performance metrics, and error aggregation. It generates structured reports in multiple formats (JSON, HTML, Markdown) for both human review and machine processing.

## Architecture

### Module Structure

```
infrastructure/reporting/
├── __init__.py              # Public API exports
├── pipeline_reporter.py     # Pipeline report generation
├── error_aggregator.py      # Error collection and categorization
├── html_templates.py        # HTML report templates
├── executive_reporter.py    # Cross-project metrics and summaries
├── dashboard_generator.py   # Visual dashboard generation
├── manuscript_overview.py   # Manuscript PDF page overview generation
├── README.md                # Quick reference
└── AGENTS.md                # This file
```

### Design Principles

1. **Multi-Format Output**: All reports generated in JSON, HTML, and Markdown
2. **Structured Data**: Machine-readable formats for programmatic access
3. **Actionable Insights**: Reports include recommendations and fixes
4. **Integration**: Seamlessly integrated into pipeline stages
5. **Error Categorization**: Intelligent error grouping and prioritization

## Core Components

### Pipeline Reporter (`pipeline_reporter.py`)

Generates consolidated reports from pipeline execution data.

#### Key Functions

**`generate_pipeline_report()`**
- Creates a `PipelineReport` dataclass from stage results
- Includes test results, validation results, performance metrics
- Supports error summaries and output statistics

**`save_pipeline_report()`**
- Saves reports in multiple formats (JSON, HTML, Markdown)
- Returns dictionary mapping format to file path
- Creates output directory if needed

**`generate_markdown_report()`**
- Generates human-readable Markdown report
- Includes summary statistics, stage details, recommendations

**`generate_html_report()`**
- Generates styled HTML report
- Includes visual indicators (status badges, summary cards)
- Responsive design for browser viewing

#### Usage Example

```python
from infrastructure.reporting import generate_pipeline_report, save_pipeline_report
from pathlib import Path

# Collect stage results
stage_results = [
    {'name': 'setup', 'exit_code': 0, 'duration': 2.5},
    {'name': 'tests', 'exit_code': 0, 'duration': 45.2},
    {'name': 'analysis', 'exit_code': 0, 'duration': 12.8},
]

# Generate report
report = generate_pipeline_report(
    stage_results=stage_results,
    total_duration=60.5,
    repo_root=Path("."),
    test_results={'summary': {'total_tests': 878, 'total_passed': 878}},
    validation_results={'checks': {'pdf_validation': True}},
    performance_metrics={'total_duration': 60.5},
)

# Save reports
saved_files = save_pipeline_report(report, Path("output/reports"))
# Returns: {'json': Path(...), 'html': Path(...), 'markdown': Path(...)}
```

### Error Aggregator (`error_aggregator.py`)

Collects, categorizes, and provides actionable fixes for errors and warnings.

#### Key Classes

**`ErrorAggregator`**
- Main class for error collection
- Categorizes errors by type
- Generates actionable fixes with priority levels
- Saves reports in JSON and Markdown formats

**`ErrorEntry`**
- Dataclass representing a single error or warning
- Includes type, message, stage, file, line, severity
- Supports suggestions and context

#### Usage Example

```python
from infrastructure.reporting import get_error_aggregator
from pathlib import Path

aggregator = get_error_aggregator()

# Add errors during pipeline execution
aggregator.add_error(
    error_type='test_failure',
    message='Test test_example failed with assertion error',
    stage='tests',
    file='tests/test_example.py',
    line=42,
    severity='error',
    suggestions=[
        'Review test output for details',
        'Check test data and fixtures',
        'Verify recent code changes',
    ],
)

aggregator.add_error(
    error_type='validation_error',
    message='PDF validation failed: missing figures',
    stage='validation',
    severity='error',
    suggestions=[
        'Check figure generation scripts',
        'Verify figure paths in manuscript',
    ],
)

# Generate summary
summary = aggregator.get_summary()
# Returns: {
#     'total_errors': 2,
#     'errors_by_type': {'test_failure': 1, 'validation_error': 1},
#     'actionable_fixes': [...],
#     ...
# }

# Save reports
aggregator.save_report(Path("output/reports"))
# Creates: error_summary.json and error_summary.md
```

#### Error Types

Common error types:
- `test_failure` - Test execution failures
- `validation_error` - Validation check failures
- `stage_failure` - Pipeline stage failures
- `build_error` - Build process errors
- `configuration_error` - Configuration issues

### Executive Reporter (`executive_reporter.py`)

Generates comprehensive cross-project metrics and executive summaries.

#### Key Functions

**`collect_manuscript_metrics(manuscript_dir: Path) -> ManuscriptMetrics`**
- Parses markdown files for word counts, sections, equations
- Detects figures, citations, and references
- Returns structured manuscript metrics

**`collect_codebase_metrics(src_dir: Path, scripts_dir: Optional[Path]) -> CodebaseMetrics`**
- Analyzes Python files for lines of code, methods, classes
- Separates source code from scripts
- Uses AST parsing for accurate code metrics

**`collect_test_metrics(reports_dir: Path) -> TestMetrics`**
- Loads test results from JSON reports
- Extracts pass/fail counts, coverage percentages
- Calculates execution times and test files

**`collect_output_metrics(output_dir: Path) -> OutputMetrics`**
- Counts PDFs, figures, data files, slides
- Calculates file sizes and totals
- Enumerates web outputs and other artifacts

**`collect_pipeline_metrics(reports_dir: Path) -> PipelineMetrics`**
- Analyzes pipeline execution reports
- Identifies bottleneck stages and durations
- Counts passed/failed stages

**`generate_executive_summary(repo_root: Path, project_names: List[str]) -> ExecutiveSummary`**
- Orchestrates metrics collection across all projects
- Generates aggregate statistics and comparisons
- Creates recommendations based on metrics
- Returns complete ExecutiveSummary dataclass

**`save_executive_summary(summary: ExecutiveSummary, output_dir: Path) -> Dict[str, Path]`**
- Saves reports in JSON, HTML, and Markdown formats
- Returns dictionary mapping format to file path
- Creates output directory if needed

#### Usage Example

```python
from infrastructure.reporting import generate_executive_summary, save_executive_summary
from pathlib import Path

repo_root = Path(".")
project_names = ["project", "small_code_project", "small_prose_project"]

# Generate comprehensive summary
summary = generate_executive_summary(repo_root, project_names)

print(f"Total projects: {summary.total_projects}")
print(f"Total manuscript words: {summary.aggregate_metrics['manuscript']['total_words']:,}")
print(f"Average test coverage: {summary.aggregate_metrics['tests']['average_coverage']:.1f}%")

# Save reports
saved_files = save_executive_summary(summary, Path("output/executive_summary"))
# Returns: {'json': Path(...), 'html': Path(...), 'markdown': Path(...)}
```

### Dashboard Generator (`dashboard_generator.py`)

Creates visual dashboards and charts for executive reporting.

#### Chart Functions

**Matplotlib Charts** (PNG/PDF)
- `create_test_count_chart()` - Bar chart of test counts by project
- `create_coverage_chart()` - Coverage percentages with threshold line
- `create_pipeline_duration_chart()` - Stacked bars of stage durations
- `create_output_distribution_chart()` - Pie chart of output types
- `create_manuscript_size_chart()` - Bar chart of word counts
- `create_summary_table()` - Professional table with key metrics

**Interactive Charts** (Plotly HTML)
- `generate_plotly_dashboard()` - Multi-tab interactive dashboard
- Hover tooltips with detailed metrics
- Zoom and pan functionality
- Responsive design

#### Usage Example

```python
from infrastructure.reporting import generate_all_dashboards, generate_executive_summary
from pathlib import Path

# Generate executive summary
summary = generate_executive_summary(Path("."), ["project1", "project2"])

# Create all dashboard formats
dashboard_files = generate_all_dashboards(summary, Path("output/executive_summary"))
# Returns: {'png': Path(...), 'pdf': Path(...), 'html': Path(...)}

print(f"Generated {len(dashboard_files)} dashboard files")
for fmt, path in dashboard_files.items():
    print(f"  {fmt.upper()}: {path.name}")
```

### Manuscript Overview Generator (`manuscript_overview.py`)

Generates visual overviews of manuscript PDFs by extracting and arranging all pages as thumbnails in a grid layout.

#### Key Functions

**`extract_pdf_pages_as_images(pdf_path: Path, dpi: int = 150) -> List[PIL.Image]`**
- Extracts each PDF page as a PIL Image object
- Uses pypdf for PDF reading and PIL for image rendering
- Supports fallback rendering if advanced libraries unavailable
- Returns list of PIL Images, one per page

**`create_page_grid(images: List[PIL.Image], cols: int = 4, padding: int = 10, max_thumb_size: Tuple[int, int] = (600, 800)) -> PIL.Image`**
- Arranges page images in a 4-column grid layout
- Automatically calculates rows based on number of pages
- Maintains aspect ratio and scales images appropriately
- Adds page numbers as labels on each thumbnail
- Returns single PIL Image containing the complete grid

**`generate_manuscript_overview(pdf_path: Path, output_dir: Path, project_name: str, dpi: int = 150) -> Dict[str, Path]`**
- Main orchestration function for manuscript overview generation
- Extracts pages, creates grid, saves both PNG and PDF outputs
- Returns dictionary mapping filename to output file path
- Handles errors gracefully and provides informative logging

**`generate_all_manuscript_overviews(summary: ExecutiveSummary, output_dir: Path, repo_root: Path) -> Dict[str, Path]`**
- Generates manuscript overviews for all projects in executive summary
- Searches multiple possible locations for manuscript PDFs
- Returns dictionary of all generated files (PNG and PDF for each project)
- Automatically integrated into `generate_all_dashboards()`

#### Implementation Details

**PDF Processing Strategy:**
1. **Primary**: Uses pypdf to read PDF pages, then renders text content using PIL drawing
2. **Advanced Fallback**: Attempts reportlab-based rendering for higher quality (if available)
3. **Simple Fallback**: Basic text extraction and PIL rendering if advanced rendering fails

**Grid Layout Algorithm:**
- Fixed 4-column layout with automatic row calculation
- Thumbnail sizing: Maintains aspect ratio, fits within max_thumb_size bounds (600x800 default)
- Page numbering: Sequential labels ("Page 1", "Page 2", etc.) on each thumbnail
- Spacing: Configurable padding between thumbnails

**Error Handling:**
- Missing PDF files: Logged as warning, project skipped
- Corrupted PDFs: Logged as error, project skipped
- Rendering failures: Graceful fallback to simpler rendering methods
- Missing dependencies: Clear error messages with installation guidance

#### Usage Example

```python
from infrastructure.reporting.manuscript_overview import generate_manuscript_overview
from pathlib import Path

# Generate overview for single project
pdf_path = Path("output/project/pdf/project_combined.pdf")
output_dir = Path("output/executive_summary")
result = generate_manuscript_overview(pdf_path, output_dir, "my_project")

# Result contains: {'manuscript_overview_my_project.png': Path(...), 'manuscript_overview_my_project.pdf': Path(...)}

# Generate for all projects (integrated into dashboard generation)
from infrastructure.reporting import generate_all_dashboards
dashboard_files = generate_all_dashboards(summary, output_dir)
# Automatically includes manuscript overviews
```

#### Output Formats

- **PNG**: High-resolution raster image (300 DPI default, print quality)
- **PDF**: Vector format preserving quality (using reportlab, if available)
- **Grid Layout**: 4-column arrangement with automatic rows
- **Page Labels**: Sequential numbering on each thumbnail
- **File Naming**: `manuscript_overview_{project_name}.png/pdf`

#### Dependencies

**Required:**
- `pypdf>=5.0`: PDF reading and page extraction
- `pillow>=10.0.0`: Image processing and rendering

**Optional:**
- `reportlab>=4.0.0`: Enhanced PDF rendering and output (recommended)

#### Output Formats

- **PNG**: High-resolution static images (300 DPI)
- **PDF**: Vector graphics for printing and archival
- **HTML**: Interactive dashboards with Plotly (requires plotly package)

### HTML Templates (`html_templates.py`)

Reusable HTML templates for report generation.

#### Key Functions

**`get_base_html_template()`**
- Base HTML template with styling
- Responsive design
- Professional appearance

**`render_summary_cards()`**
- Renders summary statistics as cards
- Grid layout for multiple metrics

**`render_table()`**
- Renders data tables
- Supports headers and rows

## Integration Points

### Pipeline Integration

The reporting module is integrated into multiple pipeline entry points:

#### Single Project Reporting

1. **`scripts/run_all.py`**
   - Generates consolidated pipeline report at end
   - Includes all stage results, test results, validation results
   - Saves to `project/output/reports/pipeline_report.{json,html,md}`

2. **`scripts/01_run_tests.py`**
   - Generates structured test reports
   - Includes test counts, coverage metrics, execution times
   - Saves to `project/output/reports/test_results.{json,md}`

3. **`scripts/04_validate_output.py`**
   - Generates validation reports
   - Includes actionable recommendations
   - Saves to `project/output/reports/validation_report.{json,md}`

#### Multi-Project Executive Reporting

4. **`run.sh` Multi-Project Options (a, b, c, d)**
   - Automatically triggers executive reporting for 2+ projects
   - Generates comprehensive cross-project analysis
   - Saves to `output/executive_summary/` directory
   - Includes consolidated reports, dashboards, and CSV data exports

5. **`scripts/07_generate_executive_report.py`**
   - Standalone executive reporting script
   - Can be run manually for any set of completed projects
   - Orchestrates full executive reporting workflow

### Error Aggregation Integration

Error aggregator can be used throughout the pipeline:

```python
from infrastructure.reporting import get_error_aggregator

aggregator = get_error_aggregator()

try:
    run_stage()
except Exception as e:
    aggregator.add_error(
        error_type='stage_failure',
        message=str(e),
        stage='analysis',
        suggestions=['Check stage logs', 'Verify inputs'],
    )
```

## Multi-Project Executive Reporting

The reporting module now includes comprehensive multi-project executive reporting capabilities:

### Features

- **Cross-Project Metrics Aggregation**: Collects and compares metrics across multiple projects
- **Health Score Calculation**: Automated project health assessment based on test coverage, manuscript quality, and output completeness
- **Visual Dashboards**: Multiple chart types showing comparative analysis, trends, and performance metrics
- **CSV Data Export**: Machine-readable data tables for further analysis
- **Actionable Recommendations**: Intelligent suggestions based on project metrics and cross-project comparisons

### Automatic Integration

Multi-project executive reporting is automatically triggered when:

1. Using `run.sh` multi-project options (a, b, c, d) with 2+ projects
2. All projects complete successfully
3. Executive reporting runs as a final stage (non-blocking)

### Manual Execution

Executive reporting can also be run manually:

```bash
# From any directory
python3 scripts/07_generate_executive_report.py

# Or programmatically
from infrastructure.reporting import generate_multi_project_report
from pathlib import Path

files = generate_multi_project_report(
    Path("."), ["project1", "project2"], Path("output/executive_summary")
)
```

### Output Structure

```
output/executive_summary/
├── consolidated_report.json      # Machine-readable metrics & health scores
├── consolidated_report.html       # Styled HTML report with recommendations
├── consolidated_report.md         # Human-readable markdown summary
├── dashboard.png                  # Comprehensive matplotlib dashboard (9 charts)
├── dashboard.pdf                  # Vector graphics dashboard for printing
├── dashboard.html                 # Interactive Plotly dashboard (optional)
├── project_metrics.csv           # Detailed project metrics table
├── aggregate_metrics.csv         # Cross-project aggregate statistics
└── health_scores.csv             # Project health scores breakdown
```

### Health Score Calculation

Projects are automatically scored on four key dimensions:

- **Test Coverage** (40% weight): Coverage percentage with quality thresholds
- **Test Integrity** (30% weight): Test failure rates and reliability
- **Manuscript Quality** (20% weight): Content completeness and academic standards
- **Output Richness** (10% weight): Generated artifacts and deliverables

Each dimension receives a letter grade (A-F) and contributes to an overall health percentage.

### Enhanced Dashboards

The executive dashboard includes 9 comprehensive charts:

1. **Test Results**: Total, passed, and failed test counts by project
2. **Coverage Analysis**: Test coverage percentages with quality thresholds
3. **Pipeline Performance**: Execution times and bottleneck analysis
4. **Manuscript Complexity**: Word count vs equations scatter plot
5. **Output Distribution**: Pie chart of generated file types
6. **Efficiency Metrics**: PDFs generated per second of pipeline time
7. **Health Scores**: Overall project health percentages
8. **Test Efficiency**: Coverage vs execution time matrix
9. **Executive Summary**: Enhanced metrics table with aggregates

## Report Structure

### Pipeline Report

```python
@dataclass
class PipelineReport:
    timestamp: str
    total_duration: float
    stages: List[StageResult]
    test_results: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]
    error_summary: Optional[Dict[str, Any]]
    output_statistics: Optional[Dict[str, Any]]
```

### Error Summary

```python
{
    'timestamp': '2025-12-04T14:01:30',
    'total_errors': 2,
    'total_warnings': 1,
    'errors_by_type': {'test_failure': 1, 'validation_error': 1},
    'warnings_by_type': {'performance': 1},
    'errors': [...],  # List of ErrorEntry dictionaries
    'warnings': [...],  # List of ErrorEntry dictionaries
    'actionable_fixes': [
        {
            'priority': 'high',
            'issue': '1 test failure(s)',
            'actions': [...],
            'documentation': 'docs/TESTING_GUIDE.md',
        },
    ],
}
```

## Best Practices

### Error Reporting

1. **Categorize Errors**: Use consistent error types for better aggregation
2. **Provide Context**: Include file, line, stage information when available
3. **Actionable Suggestions**: Provide specific steps to fix issues
4. **Priority Levels**: Use appropriate severity levels (error, warning, info)

### Report Generation

1. **Multiple Formats**: Always generate JSON, HTML, and Markdown
2. **Structured Data**: Use consistent data structures for machine processing
3. **Human-Readable**: Ensure Markdown reports are clear and actionable
4. **Visual Indicators**: Use status badges and color coding in HTML reports

### Integration

1. **Non-Blocking**: Report generation should not fail the pipeline
2. **Graceful Degradation**: Handle missing data gracefully
3. **Performance**: Report generation should be fast (< 1s)
4. **Location**: Save all reports to `project/output/reports/`

## Testing

The reporting module has comprehensive test coverage:

```bash
# Run reporting module tests
pytest tests/infrastructure/reporting/ -v

# With coverage
pytest tests/infrastructure/reporting/ --cov=infrastructure.reporting
```

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../README.md`](../README.md) - Infrastructure layer overview
- [`../AGENTS.md`](../AGENTS.md) - Complete infrastructure documentation
- [`../../docs/ADVANCED_MODULES_GUIDE.md`](../../docs/ADVANCED_MODULES_GUIDE.md) - Advanced modules guide
















