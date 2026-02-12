# Ento-Linguistics Project Documentation

Reference materials and guides for the **Ento-Linguistic Domains** research project — studying how entomological metaphors permeate and shape scientific discourse across six analytical domains.

## Key Documents

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Technical overview of every doc in this directory |
| [development_workflow.md](development_workflow.md) | Environment setup, test commands, module paths, infrastructure patterns |
| [manuscript_style_guide.md](manuscript_style_guide.md) | Figures, citations, equations, and cross-reference examples from the actual manuscript |
| [refactor_playbook.md](refactor_playbook.md) | Module dependency map, hotspots, and safe-change recipes |
| [standards_compliance.md](standards_compliance.md) | Compliance matrix with current project metrics (778 tests, coverage, validation) |
| [testing_expansion_plan.md](testing_expansion_plan.md) | Targeted testing additions across 37 test files |
| [validation_guide.md](validation_guide.md) | Preflight, figure, and manuscript validation commands |

## Quick Access

```bash
# Run the full test suite
uv run pytest tests/ -x -q

# Validate manuscript figures and references
uv run python scripts/manuscript_preflight.py --strict

# Regenerate all research figures
uv run python scripts/generate_research_figures.py

# Run the full analysis pipeline
uv run python scripts/analysis_pipeline.py
```

## Project Architecture

```
src/
├── analysis/          # Term extraction, discourse, domain, conceptual mapping
├── core/              # Exceptions, logging, metrics, parameters, validation
├── data/              # Literature mining, data generation, data processing
├── pipeline/          # Simulation framework, reporting
└── visualization/     # Concept networks, statistical plots, figure manager
```

## See Also

- [`../src/AGENTS.md`](../src/AGENTS.md) — Source code documentation
- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) — Scripts documentation
- [`../tests/AGENTS.md`](../tests/AGENTS.md) — Test suite documentation
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript structure
