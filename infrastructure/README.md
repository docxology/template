# Infrastructure Layer - Quick Reference

Modular build, validation, and development tools organized by functionality.

## Module Overview

| Module | Purpose | Key Classes/Functions | CLI |
|--------|---------|----------------------|-----|
| **core** | Foundation utilities | `get_logger`, `load_config`, `TemplateError`, `CheckpointManager` | N/A |
| **validation** | Quality & validation | `validate_pdf_rendering`, `validate_markdown`, `verify_output_integrity` | ✅ |
| **documentation** | Figure management | `FigureManager`, `ImageManager`, `MarkdownIntegration` | ✅ |
| **build** | Build verification | `verify_build_artifacts`, `analyze_document_quality`, `generate_reproducibility_report` | N/A |
| **scientific** | Scientific utilities | `check_numerical_stability`, `benchmark_function` | ✅ |
| **literature** | Literature search | `LiteratureSearch`, `LiteratureWorkflow`, `PaperSummarizer` | ✅ |
| **llm** | LLM integration | `LLMClient`, `generate_review_with_metrics` | ✅ |
| **rendering** | Multi-format output | `RenderManager` | ✅ |
| **publishing** | Publishing tools | `extract_publication_metadata`, `publish_to_zenodo`, `ZenodoClient` | ✅ |
| **reporting** | Pipeline reporting | `generate_pipeline_report`, `get_error_aggregator` | N/A |

## Quick Start

### Using a Module

```python
# Core utilities
from infrastructure.core import get_logger, load_config
logger = get_logger(__name__)
config = load_config(Path("config.yaml"))

# Validation
from infrastructure.validation import validate_pdf_rendering
report = validate_pdf_rendering(Path("output.pdf"))

# Documentation
from infrastructure.documentation import FigureManager
fm = FigureManager()
fm.register_figure("plot.png", "Results")

# Build
from infrastructure.build import analyze_document_quality
metrics = analyze_document_quality(Path("output.pdf"))

# Scientific
from infrastructure.scientific import benchmark_function
benchmark = benchmark_function(my_algorithm, inputs)

# Literature
from infrastructure.literature import LiteratureSearch, LiteratureConfig
config = LiteratureConfig()
lit = LiteratureSearch(config)
papers = lit.search_papers("machine learning", limit=10)

# LLM
from infrastructure.llm import LLMClient
llm = LLMClient()
response = llm.apply_template("summarize_abstract", text=abstract)

# Rendering
from infrastructure.rendering import RenderManager
renderer = RenderManager()
pdf = renderer.render_pdf(Path("manuscript.tex"))

# Publishing
from infrastructure.publishing import extract_publication_metadata
metadata = extract_publication_metadata([Path("manuscript.md")])

# Reporting
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    get_error_aggregator,
    generate_test_report,
    generate_validation_report
)
report = generate_pipeline_report(stage_results, total_duration, repo_root)
saved_files = save_pipeline_report(report, Path("output/reports"))
aggregator = get_error_aggregator()
aggregator.add_error("test_failure", "Test failed", stage="tests")
aggregator.save_report(Path("output/reports"))
```

### CLI Usage

```bash
# Validation
python3 -m infrastructure.validation.cli pdf output/pdf/manuscript.pdf
python3 -m infrastructure.validation.cli markdown manuscript/

# Documentation
python3 -m infrastructure.documentation.cli generate-api project/src/

# Literature
python3 -m infrastructure.literature.cli search "quantum computing" --download

# LLM
python3 -m infrastructure.llm.cli query "Summarize quantum computing"

# Rendering
python3 -m infrastructure.rendering.cli pdf manuscript.tex
python3 -m infrastructure.rendering.cli all manuscript.tex

# Publishing
python3 -m infrastructure.publishing.cli extract-metadata manuscript/
python3 -m infrastructure.publishing.cli publish-zenodo output/ --token $ZENODO_TOKEN

# Reporting (integrated into pipeline - reports auto-generated)
# Reports saved to: project/output/reports/
```

## Core Module

**Foundation utilities used by all modules.**

```python
from infrastructure.core import (
    # Logging
    get_logger, setup_logger, log_operation,
    # Configuration
    load_config, get_config_as_dict,
    # Exceptions
    TemplateError, ValidationError, ConfigurationError
)

# Logging
logger = get_logger(__name__)
logger.info("Processing data")

# Configuration
config = load_config(Path("config.yaml"))
print(config['paper']['title'])

# Error handling
try:
    risky_operation()
except Exception as e:
    raise TemplateError("Operation failed") from e
```

## Validation Module

**Validate PDFs, Markdown, and data integrity.**

```python
from infrastructure.validation import (
    validate_pdf_rendering,
    validate_markdown,
    verify_output_integrity
)

# Validate PDF
report = validate_pdf_rendering(Path("output.pdf"))
print(f"Issues: {report['issues']['total_issues']}")

# Validate Markdown
problems, exit_code = validate_markdown("manuscript/", ".")
for problem in problems:
    print(problem)

# Verify integrity
integrity = verify_output_integrity(Path("output/"))
print(f"Files checked: {integrity.get('total_files', 0)}")
```

## Documentation Module

**Manage figures and generate API documentation.**

```python
from infrastructure.documentation import (
    FigureManager, ImageManager, MarkdownIntegration,
    build_api_index, generate_markdown_table
)

# Figure management
fm = FigureManager()
fm.register_figure("plot.png", "Results", label="fig:results")
im = ImageManager(fm)
im.insert_figure(Path("results.md"), "fig:results")

# API documentation
entries = build_api_index("project/src/")
table = generate_markdown_table(entries)
```

## Build Module

**Verify builds and analyze quality.**

```python
from infrastructure.build import (
    verify_build_artifacts,
    analyze_document_quality,
    generate_reproducibility_report
)

# Verify artifacts
verification = verify_build_artifacts(Path("output/"), {"pdf": ["*.pdf"]})

# Quality analysis
metrics = analyze_document_quality(Path("output.pdf"))
print(f"Readability: {metrics['readability_scores']}")

# Reproducibility
report = generate_reproducibility_report(Path("output/"))
```

## Scientific Module

**Scientific computing tools and best practices.**

```python
from infrastructure.scientific import (
    check_numerical_stability,
    benchmark_function,
    validate_scientific_best_practices
)

# Stability checking
stability = check_numerical_stability(algorithm, test_inputs)

# Benchmarking
benchmark = benchmark_function(algorithm, test_inputs, iterations=100)
print(f"Average time: {benchmark['mean']:.3f}s")

# Best practices
report = validate_scientific_best_practices(my_module)
```

## Literature Module

**Search and manage academic literature.**

```python
from infrastructure.literature import LiteratureSearch, LiteratureConfig

config = LiteratureConfig()
search = LiteratureSearch(config)

# Search multiple sources
papers = search.search_papers(
    query="machine learning",
    sources=["arxiv", "semanticscholar"],
    limit=10
)

# Download PDFs
for paper in papers:
    path = search.download_paper(paper)
    search.add_to_library(paper)

# Extract citations
from infrastructure.literature import PDFHandler, ReferenceManager
pdf_handler = PDFHandler()
citations = pdf_handler.extract_citations(path)
ref_manager = ReferenceManager()
bibtex = ref_manager.generate_bibtex(paper)
```

## LLM Module

**Local LLM integration with research templates.**

```python
from infrastructure.llm import LLMClient

client = LLMClient()

# Use research templates
summary = client.apply_template("summarize_abstract", text=abstract)
code_docs = client.apply_template("document_code", code=my_function)
section = client.apply_template("draft_section", topic="methods")

# Direct queries
response = client.query_model("What are the key implications?")

# Streaming responses
for chunk in client.query_model_stream("Explain quantum computing"):
    print(chunk, end='', flush=True)
```

## Rendering Module

**Generate documents in multiple formats.**

```python
from infrastructure.rendering import RenderManager

renderer = RenderManager()

# PDF rendering
pdf = renderer.render_pdf(Path("manuscript.tex"))

# All formats
outputs = renderer.render_all(Path("manuscript.tex"))
for output in outputs:
    print(f"Generated: {output}")

# Specific formats
slides = renderer.render_slides(Path("slides.md"), format="revealjs")
web = renderer.render_web(Path("manuscript.md"))
html = renderer.render_html(Path("manuscript.md"))
```

## Reporting Module

**Pipeline reporting and error aggregation.**

```python
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    get_error_aggregator,
    generate_test_report,
    generate_validation_report,
    generate_performance_report,
    generate_error_summary
)

# Generate pipeline report
report = generate_pipeline_report(
    stage_results=[...],
    total_duration=60.5,
    repo_root=Path("."),
)
saved_files = save_pipeline_report(report, Path("output/reports"))

# Generate test report
test_report = generate_test_report(
    test_results={...},
    coverage_data={...}
)

# Generate validation report
validation_report = generate_validation_report(
    validation_results={...}
)

# Aggregate errors
aggregator = get_error_aggregator()
aggregator.add_error("test_failure", "Test failed", stage="tests")
aggregator.save_report(Path("output/reports"))
```

## Publishing Module

**Publish to academic platforms and generate citations.**

```python
from infrastructure.publishing import (
    extract_publication_metadata,
    generate_citation_bibtex,
    publish_to_zenodo
)

# Extract metadata
metadata = extract_publication_metadata([Path("manuscript.md")])

# Generate citations
bibtex = generate_citation_bibtex(metadata)
apa = generate_citation_apa(metadata)
print(bibtex)

# Publish to Zenodo
doi = publish_to_zenodo(metadata, [Path("output.pdf")], token)
print(f"DOI: {doi}")

# Create GitHub release
url = create_github_release(
    tag="v1.0", name="Release 1.0", files=[Path("output.pdf")],
    token=os.getenv("GITHUB_TOKEN"), repo="owner/repo"
)
```

## Configuration

### Environment Variables

```bash
# Logging
export LOG_LEVEL=0  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR

# Metadata
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_ORCID="0000-0000-0000-1234"
export PROJECT_TITLE="My Research"

# Publishing
export ZENODO_TOKEN="..."
export GITHUB_TOKEN="..."

# LLM
export OLLAMA_HOST="http://localhost:11434"
```

### YAML Configuration

Create `project/manuscript/config.yaml`:

```yaml
paper:
  title: "Novel Framework"
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"

publication:
  doi: "10.5281/zenodo.12345678"
  license: "Apache-2.0"
```

## Testing

### Run Tests

```bash
# All infrastructure tests
pytest tests/infrastructure/ -v

# Specific module
pytest tests/infrastructure/test_validation/ -v

# With coverage report
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html
```

### Coverage

All modules have comprehensive test coverage:
- core: 100%
- validation: 100%
- documentation: 100%
- build: 100%
- scientific: 100%
- literature: 91%+
- llm: 91%+
- rendering: 91%+
- publishing: 100%
- reporting: 0% (new module, tests pending)

## Common Workflows

### Complete Research Workflow

```bash
# 1. Search literature
python3 -m infrastructure.literature.cli search "machine learning" --download

# 2. Validate manuscript
python3 -m infrastructure.validation.cli markdown manuscript/

# 3. Generate API docs
python3 -m infrastructure.documentation.cli generate-api project/src/

# 4. Render to multiple formats
python3 -m infrastructure.rendering.cli all manuscript.tex

# 5. Validate quality
python3 -m infrastructure.validation.cli integrity output/

# 6. Publish release
python3 -m infrastructure.publishing.cli publish-zenodo output/ --title "My Research"
```

### Python API Example

```python
from pathlib import Path
from infrastructure.core import get_logger
from infrastructure.validation import validate_markdown, validate_pdf_rendering
from infrastructure.rendering import RenderManager
from infrastructure.publishing import publish_to_zenodo

logger = get_logger(__name__)

# Validate manuscript
logger.info("Validating manuscript...")
validate_markdown("manuscript/", ".")

# Render PDF
logger.info("Rendering PDF...")
renderer = RenderManager()
pdf = renderer.render_pdf(Path("manuscript.tex"))

# Validate output
logger.info("Validating output...")
report = validate_pdf_rendering(pdf)

# Publish
if not report['summary']['has_issues']:
    logger.info("Publishing...")
    doi = publish_to_zenodo(metadata, [pdf], token)
    logger.info(f"Published with DOI: {doi}")
```

## Module Navigation

For detailed information about each module:
- [`core/`](core/) - See [core/AGENTS.md](core/AGENTS.md)
- [`validation/`](validation/) - See [validation/AGENTS.md](validation/AGENTS.md)
- [`documentation/`](documentation/) - See [documentation/AGENTS.md](documentation/AGENTS.md)
- [`build/`](build/) - See [build/AGENTS.md](build/AGENTS.md)
- [`scientific/`](scientific/) - See [scientific/AGENTS.md](scientific/AGENTS.md)
- [`literature/`](literature/) - See [literature/AGENTS.md](literature/AGENTS.md)
- [`llm/`](llm/) - See [llm/AGENTS.md](llm/AGENTS.md)
- [`rendering/`](rendering/) - See [rendering/AGENTS.md](rendering/AGENTS.md)
- [`publishing/`](publishing/) - See [publishing/AGENTS.md](publishing/AGENTS.md)
- [`reporting/`](reporting/) - See [reporting/AGENTS.md](reporting/AGENTS.md)

## Troubleshooting

### Import Errors

Check that you're using the new module paths:

```python
# ✅ Correct
from infrastructure.validation.pdf_validator import validate_pdf_rendering
from infrastructure.documentation.figure_manager import FigureManager

# ❌ Old (won't work)
from infrastructure.pdf_validator import validate_pdf_rendering
from infrastructure.figure_manager import FigureManager
```

### Configuration Not Loading

1. Check `project/manuscript/config.yaml` exists and is valid YAML
2. Verify permissions to read file
3. Fall back to environment variables if needed

### Missing Dependencies

Install with:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Performance Tips

1. **Caching** - Results are cached when available
2. **Streaming** - Use streaming APIs for large outputs
3. **Batching** - Process multiple items efficiently
4. **Parallel** - Some operations support parallel execution

## Contributing

To extend infrastructure:
1. Add functionality to appropriate module
2. Add comprehensive tests (meet coverage requirements)
3. Update module documentation (AGENTS.md + README.md)
4. Update this file if adding new module

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete architecture documentation
- [`../AGENTS.md`](../AGENTS.md) - System overview
- [`../README.md`](../README.md) - Project quick start
