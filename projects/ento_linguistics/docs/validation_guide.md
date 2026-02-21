# Validation Guide — Ento-Linguistics

Validation pipeline and quality gates for the Ento-Linguistic Domains project.

## Quick Validation

```bash
# Run all validations in sequence
uv run pytest tests/ -x -q && \
uv run python scripts/manuscript_preflight.py --strict && \
echo "All validations passed"
```

## Test Suite

```bash
# Full suite (778 tests, ~77s)
uv run pytest tests/ -x -q

# Specific module
uv run pytest tests/test_term_extraction.py -v

# With coverage report
uv run pytest tests/ --cov=src --cov-report=html
```

## Manuscript Preflight

```bash
# Strict mode — fail on any missing figure or reference
uv run python scripts/manuscript_preflight.py --strict

# JSON output for CI
uv run python scripts/manuscript_preflight.py --json
```

Checks performed:

- All `\includegraphics` paths resolve to existing files in `output/figures/`
- All `\ref{fig:...}` labels have matching `\label{fig:...}` definitions
- Glossary markers (`<!-- BEGIN: AUTO-API-GLOSSARY -->`) are present in `98_symbols_glossary.md`
- Bibliography command (`\bibliography{references}`) is present in `99_references.md`

## Figure Validation

```bash
# Regenerate all 5 main research figures
uv run python scripts/generate_research_figures.py

# Verify figure registry
cat output/figures/figure_registry.json

# Check per-domain figures
uv run python scripts/generate_domain_figures.py
```

Expected main figures:

| Figure | File | Min Size |
|--------|------|----------|
| Concept map | `output/figures/concept_map.png` | > 100 KB |
| Terminology network | `output/figures/terminology_network.png` | > 200 KB |
| Domain comparison | `output/figures/domain_comparison.png` | > 200 KB |
| Domain overlap heatmap | `output/figures/domain_overlap_heatmap.png` | > 100 KB |
| Anthropomorphic framing | `output/figures/anthropomorphic_framing.png` | > 100 KB |

## Quality Report

```bash
# Readability, integrity, and reproducibility snapshot
uv run python scripts/quality_report.py
```

## Pre-Commit Validation

Before committing, verify:

1. **Tests pass**: `uv run pytest tests/ -x -q`
2. **Figures current**: Check `output/figures/` timestamps match latest code changes
3. **Preflight clean**: `uv run python scripts/manuscript_preflight.py --strict`
4. **No mock data**: All figure data computed from real analysis (Jaccard co-occurrence, real confidence scores)

## CI Recommendations

```bash
# Minimum CI pipeline
uv run pytest tests/ -x -q
uv run python scripts/manuscript_preflight.py --strict --json
```

- Fail on any test failure or preflight error
- Warn on figure size regressions (file sizes dropping below expected minimums)
- Persist `output/reports/` artifacts for inspection

## See Also

- [development_workflow.md](development_workflow.md) — Environment setup and commands
- [standards_compliance.md](standards_compliance.md) — Current quality metrics
- [testing_expansion_plan.md](testing_expansion_plan.md) — Test coverage roadmap
