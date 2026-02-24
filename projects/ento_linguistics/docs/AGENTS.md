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
- **Running tests**: `uv run pytest tests/ -x -q` (923 tests passing)
- **Module structure**: Five `src/` subpackages — `analysis/` (12 modules), `core/` (7), `data/` (4), `pipeline/` (2), `visualization/` (5)
- **Key scripts**: `01_build_corpus.py`, `02_generate_figures.py` (pipeline entry points); all other scripts prefixed with `_`
- **Infrastructure patterns**: Local `src/` utilities (logging, exceptions, validation) — no `infrastructure.*` imports
- **Clean slate**: `02_generate_figures.py` wipes `output/figures/` and `output/data/` before every run

### [manuscript_style_guide.md](manuscript_style_guide.md)

Documents manuscript conventions with examples drawn from the actual manuscript files:

- **Figures**: All 11 generated figures with real captions and labels
- **Equations**: Term extraction confidence, Shannon entropy, CACE scoring, Jaccard co-occurrence
- **Citations**: Real bibliography entries (Foucault, Hölldobler & Wilson, Lakoff & Johnson)
- **Section numbering**: 01–06 main, S01–S04 supplemental, 98–99 references
- **Config**: Real `config.yaml` metadata (title, author, keywords)

### [refactor_playbook.md](refactor_playbook.md)

Module dependency map and refactoring guidance:

- **Hotspots**: Largest modules (`domain_analysis.py` 40 KB, `concept_visualization.py` 39 KB, `conceptual_mapping.py` 37 KB)
- **Dependencies**: How `scripts/` depend on `src/analysis/` and `src/visualization/`
- **Risks**: Visualization font enforcement, shared domain computation patterns
- **Recipes**: Adding a new domain, modifying term extraction, extending visualizations

### [standards_compliance.md](standards_compliance.md)

Compliance matrix mapping project practices to quality standards:

- **Testing**: 923 tests passing, no mocks, real data fixtures, 40 test files
- **Code quality**: Type hints, docstrings, structured logging, deterministic seeds (`random_state=42`)
- **Manuscript**: 11 real figures, equation environments, cross-references, figure registry
- **Corpus**: 362 documents, 48,062 tokens, 871 extracted terms (223 domain-assigned), 6 concepts / 8 relationships
- **Last verified**: 2026-02-24

### [testing_expansion_plan.md](testing_expansion_plan.md)

Planned test coverage improvements across 40 existing test files:

- **Integration tests**: Pipeline script end-to-end validation
- **Property tests**: Shape/NaN guards for data generation and term extraction
- **Performance tests**: Bounded execution time for analysis modules
- **Regression fixtures**: Golden datasets for statistical validation

### [validation_guide.md](validation_guide.md)

Validation pipeline and quality gates:

- **Preflight**: `scripts/_manuscript_preflight.py` — figure existence, glossary markers, bibliography
- **Figures**: `output/figures/figure_registry.json` verification (11 figures, SHA integrity hashes)
- **Tests**: `uv run pytest tests/ -x -q` as gating step
- **Quality**: `scripts/_quality_report.py` for readability and integrity metrics
- **Clean-slate**: `02_generate_figures.py` always wipes stale output before validating figure generation

## See Also

- [`../src/AGENTS.md`](../src/AGENTS.md) — Source code modules
- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) — Script documentation
- [`../tests/AGENTS.md`](../tests/AGENTS.md) — Test organization
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript structure
