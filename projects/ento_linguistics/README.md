# Ento-Linguistic Research Project

Complete, self-contained research project examining how language shapes scientific understanding in entomology through systematic analysis of terminology networks across six Ento-Linguistic domains.

## Research Overview

This project investigates the entanglement of speech and thought in entomological research by analyzing how scientific terminology creates conceptual frameworks, framing assumptions, and communication patterns that influence research practice.

**Six Core Domains:**
1. **Unit of Individuality** - Ant vs. colony vs. superorganism
2. **Behavior and Identity** - Foraging behavior vs. forager identity
3. **Power & Labor** - Caste, queen, worker terminology structures
4. **Sex & Reproduction** - Gender concepts in ant reproduction
5. **Kin & Relatedness** - Kinship terminology in social insects
6. **Economics** - Market logic in colony resource allocation

## Project Structure

```
project/
├── src/                    # Ento-Linguistic analysis algorithms
├── tests/                  # Comprehensive test suite (90%+ coverage)
├── scripts/                # Analysis pipelines and workflows
├── manuscript/             # Research manuscript on language in entomology
├── docs/                   # Analysis documentation and guidelines
└── output/                 # Generated analyses, figures, and reports
```

## Quick Start

### Install Dependencies
```bash
cd project
pip install -e .
# or with uv:
uv sync
```

### Run Tests
```bash
pytest tests/ --cov=src
```

### Run Analysis Scripts
```bash
python3 project/scripts/example_figure.py
python3 scripts/analysis_pipeline.py
```

### Build Manuscript
```bash
cd ..
python3 scripts/03_render_pdf.py
```

## Recent Improvements (v2.3)

- **Enhanced Test Suite**: 484 tests passing (83.81% coverage) with real HTTP testing using pytest-httpserver
- **Performance Optimizations**: O(n) complexity improvements in term extraction algorithms
- **Input Validation**: Comprehensive validation across all core methods with informative error messages
- **Robust Error Handling**: Graceful degradation in rendering and infrastructure components
- **URL Encoding**: Proper encoding for PubMed API queries preventing failures
- **Standalone Compatibility**: Scripts work independently or with full infrastructure
- **Documentation Enhancement**: Improved API documentation with practical examples
- **Manuscript Clarity**: Enhanced explanations of technical concepts and quantitative results
- **Additional Test Coverage**: New tests for validation framework methods improving coverage

## Refactor & Extension Quickstart
- Read `project/docs/refactor_playbook.md` for the safe-change checklist.
- See `project/docs/refactor_hotspots.md` for current dependency hotspots.
- Use script CLIs with `--dry-run` to verify wiring (`scripts/analysis_pipeline.py`, `scripts/generate_scientific_figures.py`).
- Run `project/scripts/manuscript_preflight.py --strict` before rendering PDFs to catch missing assets.
- Add new logic in `src/`, keep `scripts/` thin, and extend tests alongside changes.

## Scientific Contributions

**Ento-Linguistic Analysis Framework:**
- **Six-domain taxonomy** for analyzing terminology in entomological research
- **Mixed-methodology approach** combining computational text analysis with theoretical discourse examination
- **Terminology network analysis** revealing structural patterns in scientific language
- **Domain-specific insights** into how language shapes scientific understanding

**Key Domains Analyzed:**
1. **Unit of Individuality** - Biological vs. social individuality concepts
2. **Behavior and Identity** - How behavioral descriptions create categorical identities
3. **Power & Labor** - Hierarchical terminology in social insect research
4. **Sex & Reproduction** - Gender concepts applied to insect reproductive biology
5. **Kin & Relatedness** - Kinship terminology in social insect societies
6. **Economics** - Market logic in colony resource allocation

## Reproducibility & Data Availability

**Reproducible Analysis:**
- All computational methods include seeded randomness for deterministic results
- Complete codebase with comprehensive test suite (83.81% coverage)
- Detailed documentation of algorithms and methodological choices
- Version-controlled environment specifications

**Data Sources:**
- PubMed API integration for real-time literature access
- arXiv API for preprint literature
- Cached search results to minimize redundant API calls
- Structured corpus management with serialization support

**Code Availability:**
- Complete Python implementation with type hints
- Modular architecture supporting extension and reuse
- Comprehensive error handling and input validation
- Cross-platform compatibility (macOS, Linux, Windows)

## Features

- **Test coverage** - Comprehensive test suite with real data testing (484 tests passing, 22 skipped, 83.74% coverage)
- **Modular design** - Clean separation of concerns with 12+ specialized modules
- **Real HTTP testing** - Uses pytest-httpserver for genuine PubMed/arXiv API interactions (no mocks)
- **Performance optimized** - Efficient algorithms with O(n) complexity improvements and single-pass processing
- **Input validation** - Robust error handling with comprehensive input validation across all methods
- **Reproducible** - Deterministic computation with seeded randomness
- **Documented** - Comprehensive documentation with detailed API references and examples
- **Robust error handling** - Graceful degradation and informative error messages with actionable suggestions
- **Portable** - Complete project in one folder, copy to use elsewhere

## Project Architecture

```mermaid
graph TB
    subgraph ProjectStructure["Project Structure"]
        SRC[src/<br/>Scientific Algorithms<br/>Data Processing<br/>Analysis & Visualization]
        TESTS[tests/<br/>Unit Tests<br/>Integration Tests<br/>100% Coverage]
        SCRIPTS[scripts/<br/>Analysis Scripts<br/>Thin Orchestrators<br/>Figure Generation]
        MANUSCRIPT[manuscript/<br/>Research Content<br/>Markdown Sections<br/>LaTeX Preamble]
        OUTPUT[output/<br/>Generated Files<br/>PDFs, Figures, Data<br/>Disposable]
        DOCS[docs/<br/>Project Documentation<br/>Architecture Notes<br/>Development Guides]
    end

    subgraph Workflow["Development Workflow"]
        DEVELOP[1. Develop<br/>src/ modules<br/>with tests]
        ORCHESTRATE[2. Create<br/>scripts/<br/>orchestrators]
        DOCUMENT[3. Write<br/>manuscript/<br/>content]
        BUILD[4. Run<br/>pipeline<br/>generate outputs]
    end

    subgraph Pipeline["Build Pipeline"]
        TEST_RUN[Test<br/>Coverage 100%]
        ANALYSIS_RUN[Analysis<br/>Execute scripts/]
        RENDER_RUN[Render<br/>PDF generation]
        VALIDATE_RUN[Validate<br/>Quality checks]
        COPY_RUN[Copy<br/>Final deliverables]
    end

    SRC --> TESTS
    SRC --> SCRIPTS
    SCRIPTS --> OUTPUT
    MANUSCRIPT --> OUTPUT
    DOCS -.-> SRC
    DOCS -.-> SCRIPTS

    DEVELOP --> ORCHESTRATE
    ORCHESTRATE --> DOCUMENT
    DOCUMENT --> BUILD

    BUILD --> TEST_RUN
    TEST_RUN --> ANALYSIS_RUN
    ANALYSIS_RUN --> RENDER_RUN
    RENDER_RUN --> VALIDATE_RUN
    VALIDATE_RUN --> COPY_RUN

    classDef primary fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef workflow fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef pipeline fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class SRC,TESTS,SCRIPTS,MANUSCRIPT,OUTPUT,DOCS primary
    class DEVELOP,ORCHESTRATE,DOCUMENT,BUILD workflow
    class TEST_RUN,ANALYSIS_RUN,RENDER_RUN,VALIDATE_RUN,COPY_RUN pipeline
```

## Quick Usage Examples

### Basic Term Extraction
```python
from src.term_extraction import TerminologyExtractor

# Extract terms from entomological texts
extractor = TerminologyExtractor()
texts = [
    "Ant colonies exhibit complex social behavior with division of labor.",
    "The queen ant lays eggs while worker ants forage for food.",
    "Eusocial insects demonstrate sophisticated communication patterns."
]

terms = extractor.extract_terms(texts, min_frequency=2)
for term_name, term_obj in terms.items():
    print(f"Term: {term_name}, Frequency: {term_obj.frequency}, Domains: {term_obj.domains}")
```

### Literature Mining
```python
from src.literature_mining import PubMedMiner, LiteratureCorpus

# Search PubMed for entomological research
miner = PubMedMiner()
pmids = miner.search("ant colony behavior", max_results=50)

# Fetch publication details
publications = miner.fetch_publications(pmids[:5])  # Get first 5
corpus = LiteratureCorpus(publications)

# Analyze the corpus
stats = corpus.get_statistics()
print(f"Corpus contains {stats['total_publications']} publications")
```

### Domain Analysis
```python
from src.domain_analysis import DomainAnalyzer
from src.term_extraction import TerminologyExtractor

# Extract terms and analyze domains
extractor = TerminologyExtractor()
terms = extractor.extract_terms(texts, min_frequency=2)

analyzer = DomainAnalyzer()
domain_analyses = analyzer.analyze_all_domains(terms, texts)

for domain_name, analysis in domain_analyses.items():
    print(f"Domain: {domain_name}")
    print(f"Key terms: {analysis.key_terms[:3]}")
    print(f"Ambiguities found: {len(analysis.ambiguities)}")
```

## Project Layout

### src/
Scientific code implementing algorithms, data processing, analysis, and visualization.

- `term_extraction.py` - Terminology extraction with domain classification
- `literature_mining.py` - PubMed/arXiv search and corpus management
- `domain_analysis.py` - Six-domain Ento-Linguistic analysis
- `discourse_analysis.py` - Rhetorical pattern and framing analysis
- `conceptual_mapping.py` - Concept network construction and analysis
- `concept_visualization.py` - Network visualization (requires networkx)
- ... and more specialized modules

### tests/
Comprehensive test suite covering src/ modules (78%+ coverage).

- Real data testing (no mocks)
- Integration tests
- Performance validation
- 460+ tests passing

### scripts/
Thin orchestrators that use src/ modules.

- Import from src/
- Orchestrate workflows
- Generate outputs

### manuscript/
Research manuscript in Markdown format.

- Individual sections
- References and bibliography
- Configuration files

## Development

### Adding New Features

1. **Implement in src/**
   - Add module to `src/`
   - Add comprehensive tests
   - Ensure coverage requirements met

2. **Use in scripts/**
   - Import from src/
   - Orchestrate analysis
   - Generate figures/tables

3. **Document in manuscript/**
   - Update manuscript sections
   - Add figures and results
   - Update configuration

### Running Quality Checks

```bash
# Full test suite with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Quality Validation

- Preflight: `python3 project/scripts/manuscript_preflight.py --strict`
- Quality report: `python3 project/scripts/quality_report.py`
- Markdown/PDF: `python3 -m infrastructure.validation.cli markdown project/manuscript/ --strict` and `python3 -m infrastructure.validation.cli pdf project/output/pdf/`
- Outputs: `python3 - <<'PY'\nfrom infrastructure.validation import verify_output_integrity\nfrom pathlib import Path\nverify_output_integrity(Path('output'))\nPY`

## Deployment

### Standalone Use
Copy `project/` to any location to use independently:

```bash
cp -r project/ /path/to/my_research
cd /path/to/my_research
pytest tests/ --cov=src
```

### Integration with Template
This project is designed to work with the template infrastructure:

```bash
cd /path/to/template
python3 scripts/03_render_pdf.py  # Builds manuscript PDFs
```

## Dependencies

- Python 3.10+
- NumPy, SciPy, Matplotlib, Pandas
- pytest, pytest-cov

See `pyproject.toml` for complete dependencies.

## Documentation

- `AGENTS.md` - Architecture and module documentation
- `docs/` - Additional project-specific documentation
- Docstrings in source code

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete project documentation
- [`src/README.md`](src/README.md) - Scientific code overview
- [`scripts/README.md`](scripts/README.md) - Analysis scripts guide
- [`tests/README.md`](tests/README.md) - Test suite overview
- [`manuscript/README.md`](manuscript/README.md) - Manuscript guide
- [`../../AGENTS.md`](../../AGENTS.md) - Complete system documentation
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Infrastructure layer

## License

See LICENSE file in template root.



