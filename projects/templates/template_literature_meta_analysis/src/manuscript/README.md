# Manuscript Template Engine

Variable computation and injection for the literature meta-analysis manuscript.
Reads pipeline output JSONs and produces a `dict[str, str]` of 127+ template variables
that `scripts/05_inject_variables.py` substitutes into `{{VAR}}` placeholders in every
`manuscript/*.md` file, writing rendered copies to `output/manuscript/`.

## Module

### `variables.py`
Single entry point: `compute_variables(output_dir: Path) -> dict[str, str]`.

Reads from `output_dir/` (or `output_dir/data/`):
| JSON file | Variables computed |
|---|---|
| `corpus.jsonl` | `CORPUS_SIZE`, `YEAR_START_PUBS`, `YEAR_END_PUBS`, `TOTAL_REFERENCES` |
| `temporal_analysis.json` | `YEAR_START`, `YEAR_END`, `PEAK_YEAR`, `PEAK_YEAR_PUBS`, `CAGR_PCT`, `MEAN_YOY_GROWTH_PCT`, `DOUBLING_TIME` |
| `subfield_classification.json` | `A1_COUNT`, `A2_COUNT`, `B_COUNT`, `C1–C5_COUNT`, `*_PCT` per subfield |
| `citation_network.json` | `CITATION_EDGES`, `CITATION_COMPONENTS`, `CITATION_DENSITY_PCT`, `MEAN_IN_DEGREE`, `CITATION_RESOLUTION_PCT`, `CITATION_TOTAL_REFS` |
| `hypothesis_scores.json` | `H1–H8_SCORE`, `H1–H8_SUPPORT`, `H1–H8_NEUTRAL`, `H1–H8_CONTRADICT`, `H1–H8_TOTAL` |
| `assertion_summary.json` | `TOTAL_ASSERTIONS`, `TOTAL_SUPPORT`, `TOTAL_NEUTRAL`, `TOTAL_CONTRADICT` |
| `tfidf_data.json` | `NUM_VOCAB_FEATURES`, `NUM_TOPICS` |
| `output/figures/` | `NUM_FIGURES` |

Hypothesis short aliases H1–H8 map to full IDs:
```
Hypotheses (H1, H2, ...) and their names/scope are defined in manuscript/config.yaml
H5=SCALABILITY       H6=CLINICAL_UTILITY H7=MORPHOGENESIS           H8=LANGUAGE_AIF
```

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

## Infrastructure Import Fallback

`variables.py` attempts `from infrastructure.core.logging.utils import get_logger` and
falls back to `logging.getLogger` if running outside the template monorepo. This ensures
the module works both in standalone mode and when PYTHONPATH includes the template root.

See [AGENTS.md](AGENTS.md) for agent-specific constraints.
