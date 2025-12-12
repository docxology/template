# 🔬 Advanced Modules Guide

> **Comprehensive guide** to the 7 advanced infrastructure modules

**Quick Reference:** [API Reference](../reference/API_REFERENCE.md) | [Architecture](ARCHITECTURE.md) | [Infrastructure Docs](../infrastructure/AGENTS.md) | [Module Standards](../.cursorrules/infrastructure_modules.md) | [LLM Standards](../.cursorrules/llm_standards.md)

This guide provides detailed usage instructions for the advanced modules that extend the Research Project Template with professional-grade features for integrity verification, publishing workflows, scientific computing best practices, literature search, LLM integration, multi-format rendering, and comprehensive reporting.

## Module Overview

The template includes advanced infrastructure modules that provide enterprise-grade capabilities:

| Module | Purpose | Key Features |
|--------|---------|--------------|
| **Integrity** | Output verification | File integrity, cross-reference validation, data consistency |
| **Publishing** | Academic workflows | DOI validation, citation generation, platform integration |
| **Scientific Dev** | Research best practices | Numerical stability, performance benchmarking, code quality |
| **Literature Search** | Academic literature management | Multi-source search, PDF download, BibTeX generation, library management |
| **LLM Integration** | Local LLM assistance | Ollama integration, research templates, context management, streaming |
| **Rendering System** | Multi-format output | PDF, slides, web, poster generation from single source |
| **Reporting** | Pipeline reporting | Consolidated reports, error aggregation, performance metrics |

All modules follow the thin orchestrator pattern with comprehensive test coverage.

---

## ✅ Integrity Module

**Location**: `infrastructure/validation/integrity.py`  
**Purpose**: File integrity and cross-reference validation

### Key Features

- **File Integrity**: SHA256-based verification of output files
- **Cross-Reference Validation**: LaTeX reference integrity checking
- **Data Consistency**: Format and structure validation
- **Academic Standards**: Compliance with writing standards
- **Build Artifact Verification**: Complete output validation

### Usage Examples

#### Comprehensive Integrity Check

```python
from infrastructure.validation.integrity import verify_output_integrity

# Verify entire output directory
report = verify_output_integrity("output/")

if report.overall_integrity:
    print("✅ All integrity checks passed")
else:
    print("❌ Integrity issues found:")
    for issue in report.issues:
        print(f"- {issue}")
    for warning in report.warnings:
        print(f"⚠️ {warning}")
```

#### Cross-Reference Validation

```python
from infrastructure.validation.integrity import verify_cross_references

# Check markdown files for reference integrity
markdown_files = ["manuscript/01_abstract.md", "manuscript/02_introduction.md"]
integrity_status = verify_cross_references(markdown_files)

for ref_type, is_valid in integrity_status.items():
    status = "✅" if is_valid else "❌"
    print(f"{status} {ref_type}: {'Valid' if is_valid else 'Issues found'}")
```

### Integration

```bash
# Automatic integrity validation
python3 scripts/04_validate_output.py

# Manual integrity check
python3 -m infrastructure.validation.integrity.cli output/
```

---

## 📚 Publishing Module

**Location**: `infrastructure/publishing/core.py`  
**Purpose**: Academic publishing workflow assistance

### Key Features

- **DOI Validation**: Format and checksum verification
- **Citation Generation**: BibTeX, APA, MLA formats
- **Publication Metadata**: Comprehensive metadata extraction
- **Submission Preparation**: Checklist and package creation
- **Academic Profile**: ORCID and repository integration

### Usage Examples

#### DOI Validation and Citation Generation

```python
from infrastructure.publishing.core import validate_doi, generate_citation_bibtex

# Validate DOI
doi = "10.5281/zenodo.12345678"
if validate_doi(doi):
    print("✅ Valid DOI")
else:
    print("❌ Invalid DOI")

# Generate BibTeX citation
metadata = {
    'title': 'Research Project Title',
    'authors': ['Dr. Jane Smith', 'Dr. John Doe'],
    'year': '2024',
    'doi': doi
}

bibtex = generate_citation_bibtex(metadata)
print("BibTeX citation:")
print(bibtex)
```

**Output:**
```
@article{smith2024research,
  title={Research Project Title},
  author={Smith, Jane and Doe, John},
  year={2024},
  doi={10.5281/zenodo.12345678}
}
```

#### Metadata Extraction

```python
from infrastructure.publishing.core import extract_publication_metadata

# Extract metadata from manuscript
markdown_files = ["manuscript/01_abstract.md", "manuscript/02_introduction.md"]
metadata = extract_publication_metadata(markdown_files)

print(f"Title: {metadata.title}")
print(f"Authors: {', '.join(metadata.authors)}")
print(f"DOI: {metadata.doi or 'Not specified'}")
```

### Publishing Workflow Integration

```bash
# Prepare publication package
python3 -m infrastructure.publishing.cli prepare-submission output/ --format=arxiv

# Validate publication metadata
python3 -m infrastructure.publishing.cli validate-metadata manuscript/
```

---

## 🔬 Scientific Development Module

**Location**: `infrastructure/scientific/` (modular package: stability.py, benchmarking.py, documentation.py, validation.py, templates.py)  
**Purpose**: Scientific computing best practices and tools

### Key Features

- **Numerical Stability**: Algorithm stability testing and validation
- **Performance Benchmarking**: Execution time and memory analysis
- **Scientific Documentation**: API documentation generation
- **Best Practices Validation**: Code quality assessment
- **Research Workflow Templates**: Reproducible experiment templates

### Usage Examples

#### Numerical Stability Testing

```python
from infrastructure.scientific import check_numerical_stability

# Test function stability across input ranges
def my_algorithm(x):
    return x**2 / (x + 1e-10)  # Potential numerical issues

stability_report = check_numerical_stability(
    my_algorithm,
    test_inputs=[0.0, 1e-8, 1e-6, 0.1, 1.0, 10.0],
    tolerance=1e-12
)

print(f"Stability Score: {stability_report.stability_score:.2f}")
print(f"Input Range: {stability_report.input_range}")
print(f"Expected Behavior: {stability_report.expected_behavior}")

if stability_report.recommendations:
    print("Recommendations:")
    for rec in stability_report.recommendations:
        print(f"- {rec}")
```

#### Performance Benchmarking

```python
from infrastructure.scientific import benchmark_function

# Benchmark algorithm performance
result = benchmark_function(
    my_algorithm,
    test_inputs=[0.1, 1.0, 10.0, 100.0],
    iterations=100
)

print(f"Function: {result.function_name}")
print(f"Average Execution Time: {result.execution_time:.6f}s")
print(f"Memory Usage: {result.memory_usage or 'Not measured'} MB")
print(f"Summary: {result.result_summary}")
```

### Scientific Workflow Integration

```bash
# Validate scientific code quality
python3 -m infrastructure.scientific.cli validate-code src/

# Generate performance reports
python3 -m infrastructure.scientific.cli benchmark src/algorithms.py
```

---

## Integration with Build Pipeline

Build verification and integrity checking are handled by the validation module:

```bash
# Automatic build verification
python3 scripts/04_validate_output.py

# Manual build verification
python3 -m infrastructure.validation.cli integrity output/
```

---

## 📚 Literature Search Module

**Location**: `infrastructure/literature/core.py`  
**Purpose**: Academic literature search and reference management

### Key Features

- **Multi-Source Search**: Unified search across arXiv, Semantic Scholar, and CrossRef
- **PDF Download**: Automatic paper retrieval with retry logic and fallback sources
- **Citation Extraction**: Extract citations from papers and generate BibTeX
- **BibTeX Management**: Generate and manage bibliography files
- **Reference Deduplication**: Merge results from multiple sources
- **Library Management**: Organize research papers with JSON-based indexing

### Usage Examples

#### Basic Literature Search

```python
from infrastructure.literature import LiteratureSearch

# Initialize searcher
searcher = LiteratureSearch()

# Search for papers
papers = searcher.search("machine learning", limit=10)

for paper in papers:
    print(f"{paper.title} ({paper.year})")
    print(f"  Authors: {', '.join(paper.authors)}")
    print(f"  DOI: {paper.doi or 'N/A'}")
```

#### Download and Manage Papers

```python
# Download PDF (saved as citation_key.pdf)
pdf_path = searcher.download_paper(papers[0])

# Add to library (both BibTeX and JSON index)
citation_key = searcher.add_to_library(papers[0])
print(f"Added to library with key: {citation_key}")

# Get library statistics
stats = searcher.get_library_stats()
print(f"Total papers: {stats['total_entries']}")
print(f"Total citations: {stats['total_citations']}")
```

#### Export References

```python
# Export BibTeX
searcher.export_bibtex("references.bib")

# Export library as JSON
searcher.export_library("library.json")
```

### Command Line Integration

```bash
# Search for papers
python3 -m infrastructure.literature.cli search "deep learning" --limit 20

# Search with download
python3 -m infrastructure.literature.cli search "transformers" --download

# List library
python3 -m infrastructure.literature.cli library list

# Show statistics
python3 -m infrastructure.literature.cli library stats
```

---

## 🤖 LLM Integration Module

**Location**: `infrastructure/llm/core.py`  
**Purpose**: Local LLM assistance for research workflows

### Key Features

- **Ollama Integration**: Local model support (privacy-first)
- **Template System**: Pre-built prompts for common research tasks
- **Context Management**: Multi-turn conversation handling
- **Streaming Support**: Real-time response generation
- **Model Fallback**: Automatic fallback to alternative models
- **Token Counting**: Track usage and costs

### Research Templates

- Abstract summarization
- Literature review generation
- Code documentation
- Data interpretation
- Section drafting assistance
- Citation formatting
- Technical abstract translation (Chinese, Hindi, Russian)

### Usage Examples

#### Basic LLM Query

```python
from infrastructure.llm import LLMClient

# Initialize client (reads OLLAMA_HOST, OLLAMA_MODEL from environment)
client = LLMClient()

# Simple query
response = client.query("What are the key findings in this paper?")
print(response)
```

#### Using Research Templates

```python
# Apply research template
summary = client.apply_template(
    "summarize_abstract",
    text=abstract_text
)

# Generate literature review section
review = client.apply_template(
    "literature_review",
    topic="machine learning",
    papers=["paper1", "paper2", "paper3"]
)
```

#### Response Modes

```python
# Short response (< 150 tokens)
answer = client.query_short("What is quantum entanglement?")

# Long response (> 500 tokens)
explanation = client.query_long("Explain quantum entanglement in detail")

# Structured JSON response
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array"}
    }
}
result = client.query_structured("Summarize...", schema=schema)
```

#### Streaming Responses

```python
# Stream response in real-time
for chunk in client.stream_query("Write a research summary"):
    print(chunk, end="", flush=True)
```

### Command Line Integration

```bash
# Check Ollama connection
python3 -m infrastructure.llm.cli check

# List available models
python3 -m infrastructure.llm.cli models

# Send query
python3 -m infrastructure.llm.cli query "What is machine learning?"

# Apply template
python3 -m infrastructure.llm.cli template summarize_abstract --input "Abstract text..."
```

---

## 🎨 Rendering System Module

**Location**: `infrastructure/rendering/core.py`  
**Purpose**: Multi-format output generation from single source

### Key Features

- **PDF Rendering**: Professional LaTeX-based PDFs
- **Presentation Slides**: Beamer (PDF) and reveal.js (HTML) slides
- **Web Output**: Interactive HTML with MathJax
- **Scientific Posters**: Large-format poster generation
- **Format-Agnostic**: Single source, multiple outputs
- **Quality Validation**: Automated output checking

### Usage Examples

#### Render All Formats

```python
from infrastructure.rendering import RenderManager
from pathlib import Path

manager = RenderManager()

# Render all formats from markdown
outputs = manager.render_all(Path("manuscript/main.md"))

# Outputs include:
# - PDF: output/pdf/main.pdf
# - Slides: output/slides/main_beamer.pdf, output/slides/main_revealjs.html
# - Web: output/web/main.html
# - Poster: output/posters/main_poster.pdf
```

#### Render Specific Format

```python
# PDF only
pdf_path = manager.render_pdf(Path("manuscript/main.tex"))

# Beamer slides
slides_pdf = manager.render_slides(
    Path("presentation.md"),
    format="beamer"
)

# Reveal.js HTML slides
slides_html = manager.render_slides(
    Path("presentation.md"),
    format="revealjs"
)

# Web version
html_path = manager.render_web(Path("manuscript/main.md"))
```

#### Combined PDF with Title Page

```python
# Render combined PDF with automatic title page generation
markdown_files = [
    Path("manuscript/01_abstract.md"),
    Path("manuscript/02_introduction.md"),
    # ... more sections
]

pdf_path = manager.render_combined_pdf(
    markdown_files,
    manuscript_dir=Path("manuscript/")
)
# Title page automatically generated from project/manuscript/config.yaml
```

### Command Line Integration

```bash
# Render all formats
python3 -m infrastructure.rendering.cli all manuscript.tex

# Render PDF only
python3 -m infrastructure.rendering.cli pdf manuscript.tex

# Generate slides
python3 -m infrastructure.rendering.cli slides presentation.md --format beamer
python3 -m infrastructure.rendering.cli slides presentation.md --format revealjs

# Generate web version
python3 -m infrastructure.rendering.cli web manuscript.md
```

---

## Integration Patterns

### Using Multiple Modules Together

```python
# Comprehensive project validation pipeline
from infrastructure.validation.integrity import verify_output_integrity
from infrastructure.publishing.core import extract_publication_metadata

def comprehensive_validation(output_dir, manuscript_files):
    """Run complete validation suite."""
    
    results = {}
    
    # 1. Integrity verification
    results['integrity'] = verify_output_integrity(output_dir)
    
    # 2. Publication metadata
    results['publishing'] = extract_publication_metadata(manuscript_files)
    
    return results

# Run comprehensive validation
results = comprehensive_validation("output/", ["manuscript/*.md"])
```

### Command Line Integration

```bash
# Quality analysis
python3 -m infrastructure.validation.cli integrity output/

# Integrity check
python3 -m infrastructure.validation.integrity.cli output/

# Publishing validation
python3 -m infrastructure.publishing.cli validate-metadata manuscript/
```

---

## 📊 Reporting Module

**Location**: `infrastructure/reporting/`  
**Purpose**: Pipeline reporting and error aggregation

### Key Features

- **Consolidated Pipeline Reports**: Multi-format reports (JSON, HTML, Markdown) with complete pipeline execution summary
- **Test Results Reporting**: Structured test reports with coverage metrics, execution times, and failure details
- **Enhanced Validation Reports**: Actionable recommendations with priority levels and issue categorization
- **Performance Metrics**: Bottleneck analysis, resource tracking, and performance warnings
- **Error Aggregation**: Categorized errors with actionable fixes and documentation links
- **HTML Templates**: Visual reports with status indicators, summary cards, and responsive design

### Usage Examples

#### Generate Pipeline Report

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
    test_results={'summary': {'total_tests': 2245, 'total_passed': 2245}},
    validation_results={'checks': {'pdf_validation': True}},
    performance_metrics={'total_duration': 60.5},
)

# Save in multiple formats
saved_files = save_pipeline_report(report, Path("output/reports"))
# Returns: {'json': Path(...), 'html': Path(...), 'markdown': Path(...)}
```

#### Aggregate Errors

```python
from infrastructure.reporting import get_error_aggregator

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

# Generate summary
summary = aggregator.get_summary()
aggregator.save_report(Path("output/reports"))
```

#### Generate Validation Report

```python
from infrastructure.reporting import generate_validation_report

validation_results = {
    'checks': {
        'pdf_validation': True,
        'markdown_validation': True,
        'output_structure': False,
    },
    'recommendations': [
        {
            'priority': 'high',
            'issue': 'Missing output directories',
            'action': 'Ensure all analysis scripts completed successfully',
            'file': 'project/output/',
        },
    ],
}

saved_files = generate_validation_report(validation_results, Path("output/reports"))
```

### Integration

The reporting module is automatically integrated into:
- `scripts/run_all.py` - Generates consolidated pipeline report at end
- `scripts/01_run_tests.py` - Generates structured test reports
- `scripts/04_validate_output.py` - Generates enhanced validation reports

Reports are saved to `project/output/reports/` by default.

### Report Formats

All reports are generated in multiple formats:
- **JSON**: Machine-readable format for programmatic access
- **HTML**: Visual format with styling for browser viewing
- **Markdown**: Human-readable format for documentation

---

## Best Practices

### 1. **Integrate Early**
Include advanced modules in your development workflow from the beginning:

```python
# In your analysis scripts
from infrastructure.validation.integrity import verify_output_integrity
from infrastructure.scientific import check_numerical_stability

# Add validation to your research pipeline
def research_workflow():
    # Your research code
    results = run_experiment()
    
    # Validate numerical stability
    stability = check_numerical_stability(my_algorithm, test_inputs)
    
    
    return results, stability, quality
```

### 2. **Automate Validation**
Set up automated validation in your build pipeline:

```bash
#!/bin/bash
# validate.sh - Comprehensive validation script


echo "✅ Verifying Integrity..."
python3 -m infrastructure.validation.integrity.cli output/

echo "📚 Validating Publishing Metadata..."
python3 -m infrastructure.publishing.cli validate-metadata manuscript/
```

### 3. **Monitor Performance**
Track module performance over time:

```python
# Performance monitoring
import time
from infrastructure.scientific import benchmark_function

def monitor_performance():
    """Track algorithm performance over time."""
    results = []
    
    for version in ["v1.0", "v1.1", "v2.0"]:
        start_time = time.time()
        result = benchmark_function(my_algorithm, test_inputs)
        end_time = time.time()
        
        results.append({
            'version': version,
            'execution_time': result.execution_time,
            'benchmark_time': end_time - start_time
        })
    
    return results
```

---

## Troubleshooting

### Common Issues

#### Integrity Validation Failures
- **File hash mismatches**: Check if outputs are deterministic
- **Cross-reference errors**: Verify all labels are properly defined
- **Data format issues**: Ensure consistent data serialization

#### Publishing Module Issues
- **DOI validation failures**: Check DOI format and checksum
- **Citation format errors**: Verify BibTeX syntax
- **Metadata extraction issues**: Ensure manuscript has proper frontmatter

---

## Module Dependencies

| Module | Dependencies | Test Coverage |
|--------|--------------|---------------|
| Integrity | hashlib, pathlib | 81% |
| Publishing | requests, bibtexparser | 86% |
| Scientific Dev | numpy, time, psutil | 88% |
| Literature Search | requests, bibtexparser | 91% |
| LLM Integration | requests, ollama | 91% |
| Rendering System | pandoc, xelatex | 91% |
| Reporting | json, pathlib | 0% (new module, tests pending) |

All modules are designed to work independently or together, with minimal coupling between components.

---

## See Also

- **[API Reference](../reference/API_REFERENCE.md)** - Complete API documentation for all modules
- **[Infrastructure Guide](../infrastructure/AGENTS.md)** - Infrastructure module architecture
- **[Build System](../operational/BUILD_SYSTEM.md)** - Build pipeline integration
- **[Scientific Simulation Guide](../modules/SCIENTIFIC_SIMULATION_GUIDE.md)** - Scientific computing patterns
- **[PDF Validation](../modules/PDF_VALIDATION.md)** - PDF quality validation workflows

---

**The advanced modules provide enterprise-grade capabilities while maintaining the template's focus on simplicity and ease of use. Each module can be used independently or integrated into comprehensive validation workflows.**
