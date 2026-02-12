# Ento-Linguistics Docs — Technical Overview

## Purpose

This directory contains project-specific documentation for the **Ento-Linguistic Domains** research project. Every file documents aspects of the actual codebase, manuscript, and workflows used in this project — not generic template patterns.

## Directory Contents

```
docs/
├── AGENTS.md                    # This file — technical overview
├── README.md                    # Quick-reference index with commands
├── development_workflow.md      # Environment setup, test/run commands, module paths
├── manuscript_style_guide.md    # Real figure, equation, and citation examples
├── refactor_playbook.md         # Module dependency map, hotspots, safe-change recipes
├── standards_compliance.md      # Compliance matrix with actual project metrics
├── testing_expansion_plan.md    # Targeted test coverage expansion
└── validation_guide.md          # Preflight, figure, and manuscript validation
```

## Document Summaries

### [development_workflow.md](development_workflow.md)

Step-by-step guide for working in the ento-linguistics codebase:

- **Environment**: `uv sync` setup, virtual environment activation
- **Running tests**: `uv run pytest tests/ -x -q` (778 tests, 7 skipped)
- **Module structure**: Five `src/` subpackages — `analysis/`, `core/`, `data/`, `pipeline/`, `visualization/`
- **Key scripts**: `analysis_pipeline.py`, `generate_research_figures.py`, `literature_analysis_pipeline.py`, `manuscript_preflight.py`
- **Infrastructure patterns**: Local `src/utils/` utilities (logging, exceptions, validation) — no `infrastructure.*` imports

### [manuscript_style_guide.md](manuscript_style_guide.md)

Documents manuscript conventions with examples drawn from the actual manuscript files:

- **Figures**: `concept_map.png`, `terminology_network.png`, `domain_comparison.png` with real captions
- **Equations**: Term extraction confidence, network adjacency, Jaccard co-occurrence
- **Citations**: Real bibliography entries (Foucault, Hölldobler & Wilson, Lakoff & Johnson)
- **Section numbering**: 01–06 main, S01–S04 supplemental, 98–99 references
- **Config**: Real `config.yaml` metadata (title, author, keywords)

### [refactor_playbook.md](refactor_playbook.md)

Module dependency map and refactoring guidance:

- **Hotspots**: Largest modules (`domain_analysis.py` 40KB, `concept_visualization.py` 39KB, `conceptual_mapping.py` 37KB)
- **Dependencies**: How `scripts/` depend on `src/analysis/` and `src/visualization/`
- **Risks**: Visualization font enforcement, shared domain computation patterns
- **Recipes**: Adding a new domain, modifying term extraction, extending visualizations

### [standards_compliance.md](standards_compliance.md)

Compliance matrix mapping project practices to quality standards:

- **Testing**: 778 tests passing, no mocks, real data fixtures
- **Code quality**: Type hints, docstrings, structured logging
- **Manuscript**: Equation environments, cross-references, figure standards
- **Validation**: Preflight checks, figure registry verification

### [testing_expansion_plan.md](testing_expansion_plan.md)

Planned test coverage improvements across 37 existing test files:

- **Integration tests**: Pipeline script end-to-end validation
- **Property tests**: Shape/NaN guards for data generation and term extraction
- **Performance tests**: Bounded execution time for analysis modules
- **Regression fixtures**: Golden datasets for statistical validation

### [validation_guide.md](validation_guide.md)

Validation pipeline and quality gates:

- **Preflight**: `scripts/manuscript_preflight.py` — figure existence, glossary markers, bibliography
- **Figures**: `output/figures/figure_registry.json` verification
- **Tests**: `uv run pytest tests/ -x -q` as gating step
- **Quality**: `scripts/quality_report.py` for readability and integrity metrics

## See Also

- [`../src/AGENTS.md`](../src/AGENTS.md) — Source code modules
- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) — Script documentation
- [`../tests/AGENTS.md`](../tests/AGENTS.md) — Test organization
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript structure
