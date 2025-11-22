# Research Project

Complete, self-contained scientific research project with integrated testing, manuscript generation, and visualization.

## Structure

```
project/
├── src/                    # Scientific code (models, analysis, utilities)
├── tests/                  # Test suite (100% coverage)
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
python scripts/example_figure.py
python scripts/analysis_pipeline.py
```

### Build Manuscript
```bash
cd ..
./repo_utilities/render_pdf.sh
```

## Features

- **100% test coverage** - All scientific code tested with real data
- **Modular design** - Clean separation of concerns
- **Reproducible** - Deterministic computation with seeded randomness
- **Documented** - Comprehensive documentation and docstrings
- **Portable** - Complete project in one folder, copy to use elsewhere

## Project Layout

### src/
Scientific code implementing algorithms, data processing, analysis, and visualization.

- `example.py` - Basic operations
- `simulation.py` - Core simulation framework
- `statistics.py` - Statistical analysis
- `data_generator.py` - Synthetic data generation
- ... and more

### tests/
Test suite with 100% coverage of src/ modules.

- Real data testing (no mocks)
- Integration tests
- Performance validation

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
   - Ensure 100% coverage

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
./repo_utilities/render_pdf.sh  # Builds manuscript PDFs
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

## License

See LICENSE file in template root.



