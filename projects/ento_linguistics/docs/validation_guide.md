# Validation Guide — Ento-Linguistics

Validation pipeline and quality gates for the Ento-Linguistic Domains project.

## Quick Validation

```bash
# Run tests then manuscript preflight
uv run pytest tests/ -x -q && \
uv run python scripts/_manuscript_preflight.py --strict && \
echo "All validations passed"
```

## Test Suite

```bash
# Full suite (948 collected; 946 pass, 1 skip; ~148s)
uv run pytest tests/ -x -q

# Specific module
uv run pytest tests/test_term_extraction.py -v
uv run pytest tests/test_semantic_entropy.py -v
uv run pytest tests/test_cace_scoring.py -v

# With coverage report
uv run pytest tests/ --cov=src --cov-report=html

# Integration tests only
uv run pytest tests/integration/ -v
```

## Figure Generation (Clean Slate)

```bash
# Stage 1: Build corpus
uv run python scripts/01_build_corpus.py

# Stage 2: Wipes output/figures/ and output/data/, regenerates all 11 figures
uv run python scripts/02_generate_figures.py

# Inspect what was generated
ls -lh output/figures/*.png
cat output/figures/figure_registry.json
```

### Expected Output (11 figures)

| Figure | File | Min Size |
|--------|------|----------|
| Concept map | `output/figures/concept_map.png` | > 100 KB |
| Terminology network | `output/figures/terminology_network.png` | > 200 KB |
| Domain comparison | `output/figures/domain_comparison.png` | > 200 KB |
| Domain overview grid | `output/figures/domain_overview_grid.png` | > 100 KB |
| Domain patterns grid | `output/figures/domain_patterns_grid.png` | > 100 KB |
| Domain overlap heatmap | `output/figures/domain_overlap_heatmap.png` | > 100 KB |
| Concept hierarchy | `output/figures/concept_hierarchy.png` | > 100 KB |
| Anthropomorphic framing | `output/figures/anthropomorphic_framing.png` | > 100 KB |
| Power & Labor ambiguities | `output/figures/power_and_labor_ambiguities.png` | > 50 KB |
| Power & Labor frequencies | `output/figures/power_and_labor_term_frequencies.png` | > 50 KB |
| Unit of Individuality patterns | `output/figures/unit_of_individuality_patterns.png` | > 50 KB |

### Expected Data Files (after `02_generate_figures.py`)

| File | Content |
|------|---------|
| `output/data/corpus_statistics.json` | Total tokens, unique tokens, avg length, top terms |
| `output/data/domain_statistics.json` | Per-domain term counts, confidence, bridging terms |
| `output/data/concept_map_summary.json` | 6 concepts, 8 relationships, per-concept term counts |
| `output/data/cace_scores.json` | Per-term CACE scores (if generated) |

## Manuscript Preflight

```bash
# Strict mode — fail on any missing figure or broken reference
uv run python scripts/_manuscript_preflight.py --strict

# JSON output for CI
uv run python scripts/_manuscript_preflight.py --json
```

Checks performed:

- All `\includegraphics` paths resolve to existing files in `output/figures/`
- All `\ref{fig:...}` labels have matching `\label{fig:...}` definitions
- Glossary markers (`<!-- BEGIN: AUTO-API-GLOSSARY -->`) are present in `98_symbols_glossary.md`
- Bibliography command (`\bibliography{references}`) is present in `99_references.md`

## Quality Report

```bash
# Readability, integrity, and reproducibility snapshot
uv run python scripts/_quality_report.py
```

## Pre-Commit Validation

Before committing, verify:

1. **Tests pass**: `uv run pytest tests/ -x -q`
2. **Figures current**: Run `uv run python scripts/02_generate_figures.py` to confirm clean-slate rebuild exits 0
3. **Preflight clean**: `uv run python scripts/_manuscript_preflight.py --strict`
4. **No mock data**: All figure data computed from real analysis (`output/data/*.json`)
5. **No hardcoded stats**: Verify `03_methodology.md` references real counts from `output/data/`

## CI Recommendations

```bash
# Minimum CI pipeline
uv run pytest tests/ -x -q
uv run python scripts/02_generate_figures.py
uv run python scripts/_manuscript_preflight.py --strict --json
```

- Fail on any test failure or preflight error
- Fail on any figure below minimum expected size
- Persist `output/reports/`, `output/figures/`, and `output/data/` as artifacts for inspection

## See Also

- [development_workflow.md](development_workflow.md) — Environment setup and commands
- [standards_compliance.md](standards_compliance.md) — Current quality metrics
- [testing_expansion_plan.md](testing_expansion_plan.md) — Test coverage roadmap
