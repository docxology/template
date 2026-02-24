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
│   ├── text_analysis.py         #   TextProcessor, LinguisticFeatureExtractor — NLP
│   ├── semantic_entropy.py      #   calculate_semantic_entropy — Shannon H(t) in bits
│   ├── cace_scoring.py          #   evaluate_term_cace — CACE 4-dimension scoring
│   ├── discourse_analysis.py    #   DiscourseAnalyzer — framing pattern analysis
│   ├── discourse_patterns.py    #   Discourse pattern definitions
│   ├── domain_analysis.py       #   DomainAnalyzer — six-domain analysis engine
│   ├── conceptual_mapping.py    #   ConceptualMapper — concept network modeling
│   ├── persuasive_analysis.py   #   Persuasive technique detection
│   ├── rhetorical_analysis.py   #   analyze_rhetorical_strategies, narrative frameworks
│   ├── performance.py           #   Convergence and scalability metrics
│   └── statistics.py            #   t_test, anova_test, CI, correlation (no mocks)
├── core/                        # Infrastructure utilities
│   ├── exceptions.py            #   Custom exception hierarchy (EntoLinguisticError)
│   ├── logging.py               #   Structured logging (get_logger)
│   ├── metrics.py               #   Quality and performance metrics
│   ├── parameters.py            #   PipelineParameters (configurable seeds, thresholds)
│   ├── validation.py            #   Result validation and quality assurance
│   ├── validation_utils.py      #   Validation helper functions
│   ├── markdown_integration.py  #   Manuscript anchor/figure scanning
│   └── example.py               #   Basic utility functions
├── data/                        # Data handling
│   ├── literature_mining.py     #   LiteratureCorpus, corpus loader
│   ├── loader.py                #   Corpus file loader
│   ├── data_generator.py        #   Synthetic data for testing
│   └── data_processing.py       #   Data preprocessing and cleaning
├── pipeline/                    # Pipeline components
│   ├── simulation.py            #   SimulationBase, SimpleSimulation
│   └── reporting.py             #   Automated report generation
└── visualization/               # Visualization modules
    ├── concept_visualization.py #   ConceptVisualizer — all 11 research figures
    ├── statistical_visualization.py # Statistical result visualization
    ├── figure_manager.py        #   FigureManager — registry, integrity hash checks
    ├── plots.py                 #   Publication-quality plot helpers
    └── visualization.py         #   VisualizationEngine — consistent styling
```

## Running Tests

```bash
# Full test suite (923 collected, ~18s)
uv run pytest tests/ -x -q

# Specific module tests
uv run pytest tests/test_term_extraction.py -v
uv run pytest tests/test_domain_analysis.py -v
uv run pytest tests/test_semantic_entropy.py -v
uv run pytest tests/test_cace_scoring.py -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Integration tests only
uv run pytest tests/integration/ -v
```

## Key Scripts

The pipeline entry points are the **non-underscore** scripts in `scripts/`:

| Script | Purpose | Command |
|--------|---------|---------|
| `01_build_corpus.py` | Corpus construction and processing | `uv run python scripts/01_build_corpus.py` |
| `02_generate_figures.py` | **Main entry point** — clears output, regenerates all 11 figures + data | `uv run python scripts/02_generate_figures.py` |

All other scripts in `scripts/` are prefixed with `_` (e.g., `_manuscript_preflight.py`, `_quality_report.py`, `_analysis_pipeline.py`) and are run directly but not auto-discovered by the pipeline:

| Script | Purpose | Command |
|--------|---------|---------|
| `_analysis_pipeline.py` | Full analysis pipeline (all stages) | `uv run python scripts/_analysis_pipeline.py` |
| `_manuscript_preflight.py` | Validate figure refs, glossary, bibliography | `uv run python scripts/_manuscript_preflight.py --strict` |
| `_quality_report.py` | Readability, integrity, reproducibility snapshot | `uv run python scripts/_quality_report.py` |
| `_conceptual_mapping_script.py` | Conceptual mapping analysis | `uv run python scripts/_conceptual_mapping_script.py` |
| `_domain_analysis_script.py` | Domain-specific analysis | `uv run python scripts/_domain_analysis_script.py` |
| `_discourse_analysis_script.py` | Discourse pattern analysis | `uv run python scripts/_discourse_analysis_script.py` |
| `_generate_domain_figures.py` | Per-domain frequency and ambiguity figures | `uv run python scripts/_generate_domain_figures.py` |
| `_literature_analysis_pipeline.py` | Full literature mining + analysis | `uv run python scripts/_literature_analysis_pipeline.py` |

> **Note**: The pipeline (via `run.sh`) auto-discovers scripts **without** the `_` prefix from `scripts/` sorted alphabetically. Scripts prefixed with `_` are excluded from auto-discovery.

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

# Semantic entropy (real TF-IDF + KMeans + Shannon entropy)
from src.analysis.semantic_entropy import calculate_semantic_entropy, HIGH_ENTROPY_THRESHOLD

# CACE scoring
from src.analysis.cace_scoring import evaluate_term_cace, compare_terms_cace
```

## Clean-Slate Pipeline Execution

`scripts/02_generate_figures.py` always starts from a clean slate — `output/figures/` and `output/data/` are wiped and recreated before any analysis runs:

```python
# In _setup_directories():
shutil.rmtree(figure_dir)  # wipe stale figures
shutil.rmtree(data_dir)    # wipe stale data
os.makedirs(figure_dir)    # recreate clean
os.makedirs(data_dir)
```

This guarantees every run produces verified, current output with no stale artefacts.

## Adding a New Analysis Module

1. Create the module in `src/analysis/new_module.py` with type hints and docstrings
2. Export key classes/functions from `src/analysis/__init__.py`
3. Add tests in `tests/test_new_module.py` — use real data, no mocks
4. Wire into `scripts/02_generate_figures.py` using the thin orchestrator pattern
5. Update `src/__init__.py` if the module should be package-level accessible

## Common Development Tasks

### Regenerate All Figures (Clean Slate)

```bash
# Wipes output/figures/ and output/data/, regenerates all 11 figures
uv run python scripts/02_generate_figures.py

# Verify figure registry
cat output/figures/figure_registry.json
```

### Build Corpus Then Generate Figures

```bash
uv run python scripts/01_build_corpus.py
uv run python scripts/02_generate_figures.py
```

### Validate Before Committing

```bash
# Tests pass
uv run pytest tests/ -x -q

# Manuscript preflight
uv run python scripts/_manuscript_preflight.py --strict

# Quality report
uv run python scripts/_quality_report.py
```

## See Also

- [README.md](README.md) — Quick reference and commands
- [validation_guide.md](validation_guide.md) — Validation pipeline details
- [refactor_playbook.md](refactor_playbook.md) — Module dependencies and safe-change recipes
- [testing_expansion_plan.md](testing_expansion_plan.md) — Test coverage roadmap
