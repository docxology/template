# Development Workflow — Ento-Linguistics

Step-by-step guide for developing in the Ento-Linguistic Domains project.

## Environment Setup

```bash
# Navigate to project root
cd projects/ento_linguistics

# Install/sync all dependencies (uses uv workspace)
uv sync

# Verify the environment
uv run python -c "import src; print(src.__version__)"
```

The project uses **uv** for dependency management. All Python commands should be run via `uv run` to ensure the correct virtual environment.

## Project Structure

```
src/
├── analysis/                    # Domain-specific analysis modules
│   ├── term_extraction.py       #   TerminologyExtractor — extract terms from corpora
│   ├── text_analysis.py         #   TextProcessor — NLP for scientific texts
│   ├── discourse_analysis.py    #   DiscourseAnalyzer — framing pattern analysis
│   ├── discourse_patterns.py    #   Discourse pattern definitions
│   ├── domain_analysis.py       #   DomainAnalysis — cross-domain comparison
│   ├── conceptual_mapping.py    #   ConceptualMapper — relationship modeling
│   ├── persuasive_analysis.py   #   Persuasive technique detection
│   ├── rhetorical_analysis.py   #   Rhetorical strategy analysis
│   ├── performance.py           #   Convergence and scalability metrics
│   └── statistics.py            #   Statistical hypothesis testing
├── core/                        # Infrastructure utilities
│   ├── exceptions.py            #   Custom exception hierarchy
│   ├── logging.py               #   Structured logging (get_logger)
│   ├── metrics.py               #   Quality and performance metrics
│   ├── parameters.py            #   Parameter management for reproducibility
│   ├── validation.py            #   Result validation and quality assurance
│   ├── validation_utils.py      #   Validation helper functions
│   ├── markdown_integration.py  #   Manuscript anchor/figure scanning
│   └── example.py               #   Basic utility functions
├── data/                        # Data handling
│   ├── literature_mining.py     #   LiteratureCorpus, PubMedMiner, ArXivMiner
│   ├── data_generator.py        #   Synthetic data for testing
│   └── data_processing.py       #   Data preprocessing and cleaning
├── pipeline/                    # Pipeline components
│   ├── simulation.py            #   SimulationBase, SimpleSimulation
│   └── reporting.py             #   Automated report generation
└── visualization/               # Visualization modules
    ├── concept_visualization.py #   ConceptVisualizer — network plots, domain comparison
    ├── statistical_visualization.py # Statistical result visualization
    ├── figure_manager.py        #   FigureManager — registry and tracking
    ├── plots.py                 #   Publication-quality plot helpers
    └── visualization.py         #   VisualizationEngine — consistent styling
```

## Running Tests

```bash
# Full test suite (778 tests, ~77s)
uv run pytest tests/ -x -q

# Specific module tests
uv run pytest tests/test_term_extraction.py -v
uv run pytest tests/test_domain_analysis.py -v
uv run pytest tests/test_discourse_analysis.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Integration tests only
uv run pytest tests/integration/ -v
```

## Key Scripts

| Script | Purpose | Example |
|--------|---------|---------|
| `analysis_pipeline.py` | Full analysis pipeline (all stages) | `uv run python scripts/analysis_pipeline.py` |
| `generate_research_figures.py` | Generate all 5 main research figures | `uv run python scripts/generate_research_figures.py` |
| `literature_analysis_pipeline.py` | Full literature mining + analysis + figures | `uv run python scripts/literature_analysis_pipeline.py` |
| `manuscript_preflight.py` | Validate figure refs, glossary, bibliography | `uv run python scripts/manuscript_preflight.py --strict` |
| `quality_report.py` | Readability, integrity, reproducibility snapshot | `uv run python scripts/quality_report.py` |
| `conceptual_mapping_script.py` | Conceptual mapping analysis | `uv run python scripts/conceptual_mapping_script.py` |
| `domain_analysis_script.py` | Domain-specific analysis | `uv run python scripts/domain_analysis_script.py` |
| `discourse_analysis_script.py` | Discourse pattern analysis | `uv run python scripts/discourse_analysis_script.py` |
| `generate_domain_figures.py` | Per-domain frequency and ambiguity figures | `uv run python scripts/generate_domain_figures.py` |

## Infrastructure Patterns

This project uses **local** `src/` utilities rather than external `infrastructure.*` imports:

```python
# Logging
from src.core.logging import get_logger
logger = get_logger(__name__)

# Exceptions
from src.core.exceptions import EntoLinguisticError

# Validation
from src.core.validation import validate_results

# Figure management
from src.visualization.figure_manager import FigureManager
fig_manager = FigureManager(output_dir="output/figures")

# Visualization
from src.visualization.concept_visualization import ConceptVisualizer
visualizer = ConceptVisualizer()
```

## Adding a New Analysis Module

1. Create the module in `src/analysis/new_module.py` with type hints and docstrings
2. Export key classes/functions from `src/analysis/__init__.py`
3. Add tests in `tests/test_new_module.py` — use real data, no mocks
4. Wire into a script in `scripts/` using the thin orchestrator pattern
5. Update `src/__init__.py` if the module should be package-level accessible

## Common Development Tasks

### Regenerate All Figures

```bash
# Main research figures (concept_map, terminology_network, domain_comparison, etc.)
uv run python scripts/generate_research_figures.py

# Per-domain frequency/ambiguity figures
uv run python scripts/generate_domain_figures.py

# Verify figure registry
cat output/figures/figure_registry.json
```

### Run the Full Pipeline

```bash
uv run python scripts/analysis_pipeline.py
```

### Validate Before Committing

```bash
# Tests pass
uv run pytest tests/ -x -q

# Manuscript preflight
uv run python scripts/manuscript_preflight.py --strict

# Quality report
uv run python scripts/quality_report.py
```

## See Also

- [README.md](README.md) — Quick reference and commands
- [validation_guide.md](validation_guide.md) — Validation pipeline details
- [refactor_playbook.md](refactor_playbook.md) — Module dependencies and safe-change recipes
- [testing_expansion_plan.md](testing_expansion_plan.md) — Test coverage roadmap
