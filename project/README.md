# Ways of Knowing Analysis Research Project

Complete, self-contained research project focused on analyzing ways of knowing using Andrius Kulikauskas's philosophical framework, with integrated testing, manuscript generation, and visualization.

## Structure

```
project/
├── src/                    # Ways analysis code (database, models, analysis)
├── tests/                  # Test suite (ways analysis coverage)
├── scripts/                # Analysis scripts (database setup)
├── manuscript/             # Ways of knowing research manuscript
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
pytest tests/ --cov=src --cov-fail-under=70
```

### Setup Database and Run Analysis
```bash
python scripts/db_setup.py  # Initialize ways database
# Analysis will be run automatically during manuscript build
```

### Build Manuscript
```bash
cd ..
python3 scripts/03_render_pdf.py
```

## Features

- **Ways of knowing analysis** - Comprehensive analysis of Andrius Kulikauskas's philosophical framework
- **Database-driven** - SQLAlchemy ORM with SQLite backend for ways data
- **Comprehensive test coverage** - All ways analysis code tested with real database data (70% minimum)
- **Modular design** - Clean separation between database, analysis, and presentation layers
- **Reproducible** - Deterministic analysis with version-controlled database schema
- **Documented** - Comprehensive documentation and docstrings for ways analysis
- **Portable** - Complete ways research project in one folder, copy to use elsewhere

## Project Layout

### src/
Ways of knowing analysis code implementing database models, analysis algorithms, and utilities.

- `database.py` - SQLAlchemy ORM for ways database
- `sql_queries.py` - Raw SQL queries for ways data
- `models.py` - Data models (Way, Room, Question, Example)
- `ways_analysis.py` - Main ways analysis framework
- `house_of_knowledge.py` - House of Knowledge analysis
- `network_analysis.py` - Network relationships between ways
- `statistics.py` - Ways-specific statistical analysis
- `metrics.py` - Ways coverage and balance metrics

### tests/
Test suite with comprehensive coverage of ways analysis modules (70% minimum).

- Real database testing (no mocks)
- Integration tests for ways workflows
- Database query validation

### scripts/
Thin orchestrators for ways database setup and analysis.

- Import from src/
- Initialize ways database
- Orchestrate ways analysis workflows

### manuscript/
Ways of knowing research manuscript in Markdown format.

- Individual sections on ways analysis
- References and bibliography
- Configuration files for ways research

## Development

### Adding New Ways Analysis Features

1. **Implement in src/**
   - Add ways analysis module to `src/`
   - Add comprehensive tests with real database data
   - Ensure 70% coverage requirements met for ways modules

2. **Use in analysis workflows**
   - Import from ways analysis modules
   - Orchestrate ways data analysis
   - Generate ways analysis figures/tables

3. **Document in manuscript**
   - Update ways research manuscript sections
   - Add ways analysis figures and results
   - Update ways research configuration

### Running Quality Checks

```bash
# Full ways analysis test suite with coverage
pytest tests/ --cov=src --cov-fail-under=70 --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Deployment

### Standalone Use
Copy `project/` to any location to use independently for ways research:

```bash
cp -r project/ /path/to/my_ways_research
cd /path/to/my_ways_research
pytest tests/ --cov=src --cov-fail-under=70
python scripts/db_setup.py  # Initialize ways database
```

### Integration with Template
This ways research project is designed to work with the template infrastructure:

```bash
cd /path/to/template
python3 scripts/03_render_pdf.py  # Builds ways manuscript PDFs
```

## Dependencies

- Python 3.10+
- SQLAlchemy (database ORM)
- NumPy, SciPy, Matplotlib, Pandas
- pytest, pytest-cov

See `pyproject.toml` for complete dependencies.

## Documentation

- `AGENTS.md` - Architecture and module documentation
- `docs/` - Additional project-specific documentation
- Docstrings in source code

## License

See LICENSE file in template root.



