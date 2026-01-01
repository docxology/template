# scripts/ - Publication and Documentation Scripts

## Overview

The `scripts/` directory contains publication preparation and documentation generation tools that demonstrate proper integration with infrastructure modules. Scripts coordinate publishing workflows, manuscript validation, and automated documentation generation.

## Key Concepts

- **Publication workflow orchestration**: Scripts manage academic publishing processes
- **Manuscript validation**: Comprehensive quality assurance for research documents
- **API documentation generation**: Automated documentation from source code
- **Mathematical analysis**: Performance monitoring and scientific validation
- **Infrastructure integration**: Leverages all infrastructure modules (performance, progress, scientific, publishing)

## Directory Structure

```
scripts/
├── prepare_publication.py      # Publication materials preparation
├── validate_manuscript.py      # Manuscript validation and quality checks
├── generate_api_docs.py        # API documentation generation
├── analysis_pipeline.py        # Mathematical analysis (existing)
├── AGENTS.md                   # This technical documentation
└── README.md                   # Quick reference
```

## Installation/Setup

Scripts require infrastructure dependencies:

- `infrastructure` - Publishing and documentation modules
- `pathlib` - Path handling (standard library)
- `json` - JSON processing (standard library)

## Usage Examples

### Publication Preparation

```python
# From project root
python3 scripts/prepare_publication.py
```

This script:
1. Extracts publication metadata from manuscript files
2. Generates citations in BibTeX, APA, and MLA formats
3. Validates DOI information and creates badges
4. Creates publication summary and announcement materials
5. Saves all materials to structured output directories

### Manuscript Validation

```python
# From project root
python3 scripts/validate_manuscript.py
```

This script:
1. Validates manuscript markdown structure and cross-references
2. Checks academic writing standards compliance
3. Verifies link integrity and URL validity
4. Assesses output directory integrity
5. Generates comprehensive validation reports

### API Documentation Generation

```python
# From project root
python3 scripts/generate_api_docs.py
```

This script:
1. Scans Python source code for API elements
2. Generates markdown documentation tables
3. Creates comprehensive API reference documentation
4. Optionally integrates documentation into manuscript
5. Saves documentation to structured output directories

### Mathematical Analysis Pipeline

```python
# From project root
python3 scripts/analysis_pipeline.py
```

This script demonstrates comprehensive infrastructure integration:
1. **Performance Monitoring**: Tracks resource usage during mathematical analysis
2. **Progress Tracking**: Visual progress indicators for multi-step operations
3. **Scientific Validation**: Numerical stability assessment and performance benchmarking
4. **Mathematical Visualization**: Generates publication-quality plots with progress feedback
5. **Error Handling**: Comprehensive exception handling with recovery suggestions
6. **Data Analysis**: Saves analysis results with structured output validation

## Configuration

Scripts use project-specific configuration:

- **Manuscript directory**: `project_root/manuscript/` for content extraction
- **Source directory**: `project_root/src/` for API documentation
- **Output directory**: `project_root/output/` for generated materials
- **Infrastructure availability**: Graceful fallback when modules unavailable

## Testing

Scripts are validated through integration tests:

```bash
# Run publication-related tests
pytest ../tests/ -k "publication" -v

# Test manuscript validation
pytest ../tests/ -k "validation" -v

# Test API documentation generation
pytest ../tests/ -k "api_docs" -v
```

## API Reference

### prepare_publication.py

#### extract_manuscript_metadata (function)
```python
def extract_manuscript_metadata() -> Optional[Dict[str, Any]]:
    """Extract publication metadata from manuscript files.

    Scans manuscript directory for markdown files and extracts
    publication metadata including title, authors, DOI, etc.

    Returns:
        Dictionary with publication metadata, or None if extraction fails
    """
```

#### generate_citations (function)
```python
def generate_citations(metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate citations in multiple academic formats.

    Args:
        metadata: Publication metadata dictionary from extract_manuscript_metadata()

    Returns:
        Dictionary with 'bibtex', 'apa', 'mla' citation strings, or None if generation fails
    """
```

#### validate_doi_info (function)
```python
def validate_doi_info(metadata: Dict[str, Any]) -> Optional[str]:
    """Validate DOI and generate markdown badge.

    Args:
        metadata: Publication metadata dictionary

    Returns:
        DOI badge markdown string for inclusion in README files, or None if validation fails
    """
```

#### create_publication_materials (function)
```python
def create_publication_materials(
    metadata: Dict[str, Any],
    citations: Dict[str, str],
    doi_badge: Optional[str]
) -> Optional[Dict[str, Path]]:
    """Create and save publication materials to output directory.

    Args:
        metadata: Publication metadata
        citations: Citation formats dictionary
        doi_badge: DOI badge markdown string

    Returns:
        Dictionary mapping material types to saved file paths, or None if creation fails
    """
```

#### main (function)
```python
def main() -> None:
    """Main publication preparation workflow.

    Orchestrates complete publication preparation:
    1. Extract manuscript metadata
    2. Generate citations in multiple formats
    3. Validate DOI and create badges
    4. Create publication materials and summaries
    5. Save all outputs to structured directories
    """
```

### validate_manuscript.py

#### validate_manuscript_structure (function)
```python
def validate_manuscript_structure() -> Optional[Dict[str, Any]]:
    """Validate manuscript markdown structure and formatting.

    Returns:
        Validation results with errors and exit code, or None if validation fails
    """
```

#### validate_cross_references (function)
```python
def validate_cross_references() -> Optional[Dict[str, bool]]:
    """Validate cross-references between manuscript sections.

    Returns:
        Dictionary mapping reference types to validation status, or None if validation fails
    """
```

#### validate_academic_standards (function)
```python
def validate_academic_standards() -> Optional[Dict[str, bool]]:
    """Validate compliance with academic writing standards.

    Returns:
        Dictionary mapping academic standards to compliance status, or None if validation fails
    """
```

#### validate_links (function)
```python
def validate_links() -> Optional[List[Dict[str, Any]]]:
    """Validate links and URL references in manuscript.

    Returns:
        List of link validation issues with details, or None if validation fails
    """
```

#### validate_output_integrity (function)
```python
def validate_output_integrity() -> Optional[Any]:
    """Validate integrity of output directory and generated files.

    Returns:
        Integrity report object with validation results, or None if validation fails
    """
```

#### save_validation_report (function)
```python
def save_validation_report(results: Dict[str, Any]) -> Optional[Dict[str, Path]]:
    """Save comprehensive validation report to output directory.

    Args:
        results: Validation results dictionary

    Returns:
        Dictionary with paths to saved report files, or None if saving fails
    """
```

#### main (function)
```python
def main() -> None:
    """Main manuscript validation workflow.

    Orchestrates comprehensive manuscript validation:
    1. Validate markdown structure and formatting
    2. Check cross-references and academic standards
    3. Verify link integrity and URL validity
    4. Assess output directory integrity
    5. Generate comprehensive validation reports
    """
```

### generate_api_docs.py

#### scan_source_code (function)
```python
def scan_source_code() -> Optional[Dict[str, Any]]:
    """Scan Python source code for API elements.

    Returns:
        Dictionary with categorized API elements (functions, classes, methods), or None if scanning fails
    """
```

#### generate_documentation_tables (function)
```python
def generate_documentation_tables(api_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate markdown documentation tables from API data.

    Args:
        api_data: API elements data from scan_source_code()

    Returns:
        Dictionary with markdown table strings by category, or None if generation fails
    """
```

#### save_documentation_files (function)
```python
def save_documentation_files(tables: Dict[str, str]) -> Optional[Dict[str, Path]]:
    """Save generated documentation tables to output directory.

    Args:
        tables: Documentation tables from generate_documentation_tables()

    Returns:
        Dictionary mapping file types to saved file paths, or None if saving fails
    """
```

#### integrate_into_manuscript (function)
```python
def integrate_into_manuscript(tables: Dict[str, str]) -> Optional[List[Path]]:
    """Integrate API documentation into manuscript files if markers exist.

    Args:
        tables: Documentation tables dictionary

    Returns:
        List of manuscript files that were updated, or None if integration fails
    """
```

#### generate_api_summary (function)
```python
def generate_api_summary(api_data: Dict[str, Any], tables: Dict[str, str]) -> Optional[Path]:
    """Generate comprehensive API documentation summary.

    Args:
        api_data: API elements data
        tables: Generated documentation tables

    Returns:
        Path to generated summary file, or None if generation fails
    """
```

#### main (function)
```python
def main() -> None:
    """Main API documentation generation workflow.

    Orchestrates complete API documentation generation:
    1. Scan source code for API elements
    2. Generate markdown documentation tables
    3. Save documentation to output directory
    4. Optionally integrate into manuscript files
    5. Generate comprehensive documentation summary
    """
```

## Output Structure

Scripts generate organized outputs in `output/` directory:

```
output/
├── citations/                  # Publication materials
│   ├── citation_bibtex.txt     # BibTeX format citation
│   ├── citation_apa.txt        # APA format citation
│   ├── citation_mla.txt        # MLA format citation
│   ├── doi_badge.md           # DOI badge for README
│   ├── publication_summary.md  # Publication summary
│   ├── publication_metadata.json # Extracted metadata
│   └── submission_checklist.md # Publishing checklist
├── reports/                    # Validation and analysis reports
│   ├── manuscript_validation.json # Validation results
│   ├── manuscript_validation.md   # Human-readable validation report
│   └── api_statistics.json       # API documentation statistics
└── docs/                       # Generated documentation
    ├── api_reference_complete.md     # Complete API reference
    ├── api_reference_functions.md    # Functions reference
    ├── api_reference_classes.md      # Classes reference
    ├── api_reference_constants.md    # Constants reference
    ├── api_documentation_summary.md  # Documentation summary
    └── api_statistics.json          # Documentation statistics
```

## Integration with Manuscript

### Automatic Integration

Scripts can automatically integrate content into manuscript files using markers:

```markdown
<!-- API_REFERENCE_BEGIN -->
<!-- Content will be inserted here -->
<!-- API_REFERENCE_END -->
```

### Manual Integration

Generated materials can be manually included in manuscripts:

```markdown
## References

See `output/citations/citation_bibtex.txt` for BibTeX citation.

## API Reference

See `output/docs/api_reference_complete.md` for complete API documentation.
```

## Troubleshooting

### Common Issues

- **Infrastructure not available**: Scripts gracefully handle missing infrastructure modules
- **Manuscript directory not found**: Ensure `manuscript/` directory exists with markdown files
- **Source directory empty**: Ensure `src/` directory contains Python files for API documentation
- **Output directory permissions**: Ensure write permissions for output directory

### Debug Tips

Enable debug output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check infrastructure availability:
```python
try:
    from infrastructure.publishing import extract_publication_metadata
    print("Infrastructure available")
except ImportError as e:
    print(f"Infrastructure not available: {e}")
```

## Infrastructure Integration

### Performance Monitoring

Resource usage tracking during mathematical analysis:

```python
from infrastructure.core.performance import monitor_performance

with monitor_performance("Prose project analysis pipeline") as monitor:
    # Main analysis execution
    demo_results = run_mathematical_demonstration()
    math_viz = generate_mathematical_visualization()

# Performance metrics are automatically logged
performance_metrics = monitor.stop()
```

### Progress Tracking

Visual progress indicators for multi-step operations:

```python
from infrastructure.core.progress import ProgressBar

# Progress tracking for mathematical tests
with ProgressBar(total=5, desc="Mathematical tests") as progress:
    demo_results = run_mathematical_demonstration_with_progress(progress)

# Progress tracking for data operations
with ProgressBar(total=1, desc="Saving data") as progress:
    data_path = save_analysis_data_with_progress(demo_results, progress)
```

### Scientific Validation

Numerical stability and performance benchmarking:

```python
from infrastructure.scientific import check_numerical_stability, benchmark_function

# Validate mathematical functions
stability_report = validate_mathematical_functions()

# Benchmark operations
benchmark_report = benchmark_mathematical_operations()

# Save validation reports
save_scientific_validation_reports(stability_report, benchmark_report)
```

### Enhanced Error Handling

Comprehensive exception handling with recovery suggestions:

```python
try:
    # Main analysis pipeline
    results = run_analysis()
except ScriptExecutionError as e:
    print(f"Script execution failed: {e}")
    if e.recovery_commands:
        print("Recovery commands:")
        for cmd in e.recovery_commands:
            print(f"  {cmd}")
except TemplateError as e:
    print(f"Infrastructure error: {e}")
    if e.suggestions:
        print("Suggestions:")
        for suggestion in e.suggestions:
            print(f"  • {suggestion}")
```

## Best Practices

- **Run scripts from project root**: Ensures correct path resolution
- **Check outputs**: Validate generated files exist and contain expected content
- **Integration markers**: Use consistent marker patterns for manuscript integration
- **Version control**: Include generated documentation in version control when appropriate
- **Regular validation**: Run validation scripts regularly during manuscript development

## See Also

- [README.md](README.md) - Quick reference guide
- [../src/](../src/) - Source code documented by scripts
- [../manuscript/](../manuscript/) - Manuscript files processed by scripts