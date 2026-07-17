# Manuscript Template Engine

Variable computation and injection for the literature meta-analysis manuscript.
Reads pipeline output JSONs and produces a `dict[str, str]` of registered template variables
that `scripts/05_inject_variables.py` substitutes into `{{VAR}}` placeholders in every
`manuscript/*.md` file, writing rendered copies to `output/manuscript/`.

## Module

### `variables/`
Package entry point: `compute_variables(output_dir: Path) -> dict[str, str]` (in `variables/compute.py`,
re-exported from `variables/__init__.py`). Submodules: `context.py`, `formatters.py`, `inject.py`,
`io.py`, `registry.py`, and per-source `extractors/`.

Reads from `output_dir/` (or `output_dir/data/`):
| JSON file | Variables computed |
|---|---|
| `corpus.jsonl` | `CORPUS_SIZE`, `YEAR_START_PUBS`, `YEAR_END_PUBS`, `TOTAL_REFERENCES` |
| `temporal_analysis.json` | `YEAR_START`, `YEAR_END`, `PEAK_YEAR`, `PEAK_YEAR_PUBS`, `CAGR_PCT`, `MEAN_YOY_GROWTH_PCT`, `DOUBLING_TIME` |
| `subfield_classification.json` | `A1_COUNT`, `A2_COUNT`, `B_COUNT`, `C1–C5_COUNT`, `*_PCT` per subfield |
| `citation_network.json` | `CITATION_EDGES`, `CITATION_COMPONENTS`, `CITATION_DENSITY_PCT`, `MEAN_IN_DEGREE`, `CITATION_RESOLUTION_PCT`, `CITATION_TOTAL_REFS` |
| `hypothesis_scores.json` + `config.yaml` | configuration-keyed `*_SCORE` values and `HYPOTHESIS_TABLE` |
| `assertion_summary.json` | `TOTAL_ASSERTIONS`, `TOTAL_SUPPORT`, `TOTAL_NEUTRAL`, `TOTAL_CONTRADICT` |
| `tfidf_data.json` | `NUM_VOCAB_FEATURES`, `NUM_TOPICS` |
| `output/figures/` | `NUM_FIGURES` |

Hypothesis identifiers are configuration-owned. The bundled instance defines four
phase-aware exoplanet-atmosphere questions. Forks must update the configuration, claim
ledger, and evidence registry together; no hypothesis names are hard-coded in the
variable package.

All numeric variables are formatted as strings ready for LaTeX insertion:
- Integers ≥ 1000: thousand-separated (e.g. `"2,795"`)
- Percentages: always `value × 100` (CAGR, growth rates)
- Scores: 3 decimal places

## Usage

```python
from manuscript.variables import compute_variables, inject_variables
from pathlib import Path

variables = compute_variables(Path("output"))
rendered = inject_variables(source_text, variables, filename="03_results_hypothesis.md")
```

## Shared Logger

`variables/_logging.py` exposes a single module-level `logger = logging.getLogger(__name__)`
that every submodule imports (`from manuscript.variables._logging import logger`), so log
output is consistently namespaced across the package.

See [AGENTS.md](AGENTS.md) for agent-specific constraints.
