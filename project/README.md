# Tree Grafting Research Project

Complete, self-contained scientific research project on tree grafting science and practice. Includes computational toolkit for graft compatibility prediction, biological process simulation, decision support systems, and comprehensive transdisciplinary review synthesizing 4,000+ years of grafting knowledge.

## Structure

```
project/
├── src/                    # Scientific code (models, analysis, utilities)
├── tests/                  # Test suite (comprehensive coverage)
├── scripts/                # Analysis scripts (thin orchestrators)
├── manuscript/             # Research manuscript sections
├── docs/                   # Project-specific documentation
└── output/                 # Generated outputs (figures, data, PDFs)
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
python3 scripts/example_figure.py
python3 scripts/analysis_pipeline.py
```

### Build Manuscript
```bash
cd ..
python3 scripts/03_render_pdf.py
```

## Refactor & Extension Quickstart
- Read `project/docs/refactor_playbook.md` for the safe-change checklist.
- See `project/docs/refactor_hotspots.md` for current dependency hotspots.
- Use script CLIs with `--dry-run` to verify wiring (`scripts/analysis_pipeline.py`, `scripts/generate_scientific_figures.py`).
- Run `project/scripts/manuscript_preflight.py --strict` before rendering PDFs to catch missing assets.
- Add new logic in `src/`, keep `scripts/` thin, and extend tests alongside changes.

## Features

### Research Contributions
- **Comprehensive review** - Synthesis of 4,000+ years of grafting knowledge
- **Computational toolkit** - Compatibility prediction, biological simulation, decision support
- **Species database** - 15+ major fruit tree species with compatibility data
- **Technique library** - Detailed protocols for 7+ grafting methods
- **Economic analysis** - Cost-benefit evaluation and productivity optimization

### Software Quality
- **Test coverage** - All scientific code tested with real data (94.34% coverage)
- **Modular design** - Clean separation of business logic and orchestration
- **Reproducible** - Deterministic computation with seeded randomness
- **Documented** - Comprehensive documentation and docstrings
- **Portable** - Complete project in one folder, copy to use elsewhere
- **Validated** - Extensive validation framework for figures, data, and outputs

## Project Layout

### src/
Scientific code implementing grafting algorithms, compatibility prediction, biological simulation, and analysis.

**Core Grafting Modules:**
- `graft_basics.py` - Fundamental grafting calculations and compatibility checks
- `biological_simulation.py` - Cambium integration and callus formation simulation
- `compatibility_prediction.py` - Multi-factor compatibility prediction algorithms
- `species_database.py` - Species compatibility database and management
- `technique_library.py` - Grafting technique encyclopedia and protocols

**Analysis Modules:**
- `graft_analysis.py` - Success factor analysis and outcome evaluation
- `graft_statistics.py` - Statistical analysis and hypothesis testing
- `economic_analysis.py` - Cost-benefit and productivity analysis
- `rootstock_analysis.py` - Rootstock selection and evaluation
- `seasonal_planning.py` - Optimal timing and climate adaptation

**Data & Visualization:**
- `graft_data_generator.py` - Realistic grafting trial data generation
- `graft_data_processing.py` - Data cleaning, normalization, and feature extraction
- `graft_visualization.py` - Publication-quality figure generation
- `graft_plots.py` - Specialized plotting functions
- `graft_metrics.py` - Performance metrics and quality measures
- `graft_reporting.py` - Automated report generation
- `graft_validation.py` - Result validation and biological constraint checking
- `graft_parameters.py` - Parameter set management and validation

### tests/
Test suite with coverage of src/ modules (100% - perfect coverage!).

- Real data testing (no mocks)
- Integration tests
- Performance validation

### scripts/
Thin orchestrators that use src/ modules for generating figures, running analyses, and validating manuscript.

**Figure Generation:**
- `basic_grafting_figures.py` - Fundamental grafting anatomy and technique diagrams
- `generate_grafting_figures.py` - Comprehensive grafting analysis figures
- `generate_manuscript_figures.py` - Manuscript-specific visualizations
- `generate_biological_figures.py` - Biological process illustrations

**Analysis Pipelines:**
- `graft_analysis_pipeline.py` - Complete grafting analysis workflow
- `biological_process_simulation.py` - Biological simulation execution

**Quality Assurance:**
- `manuscript_preflight.py` - Pre-render validation (figures, glossary, references)
- `quality_report.py` - Comprehensive quality metrics and integrity checks

### manuscript/
Comprehensive research manuscript on tree grafting science and practice.

**Main Sections:**
- `01_abstract.md` - Research overview and contributions
- `02_introduction.md` - Historical context and project structure
- `03_methodology.md` - Biological mechanisms, techniques, and computational framework
- `04_experimental_results.md` - Compatibility analysis and validation
- `05_discussion.md` - Biological insights and applications
- `06_conclusion.md` - Summary and future directions
- `08_acknowledgments.md` - Recognition of knowledge sources
- `09_appendix.md` - Technical details and protocols

**Supplemental Material:**
- `S01_supplemental_methods.md` - Extended technique protocols
- `S02_supplemental_results.md` - Additional experimental data
- `S03_supplemental_analysis.md` - Molecular and statistical extensions
- `S04_supplemental_applications.md` - Application case studies

**References:**
- `98_symbols_glossary.md` - Auto-generated API reference
- `99_references.md` - Bibliography
- `references.bib` - BibTeX database
- `config.yaml` - Paper metadata and configuration

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

**Core Scientific Computing:**
- Python 3.10+
- NumPy - Numerical arrays and computation
- SciPy - Statistical analysis and optimization
- Matplotlib - Visualization and figure generation
- Pandas - Data manipulation (optional)

**Testing:**
- pytest - Test framework
- pytest-cov - Coverage reporting

**Documentation:**
- Pandoc - Markdown to PDF conversion
- XeLaTeX - PDF rendering with LaTeX
- BasicTeX or MacTeX - LaTeX distribution

See `pyproject.toml` for complete dependency list and version specifications.

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



