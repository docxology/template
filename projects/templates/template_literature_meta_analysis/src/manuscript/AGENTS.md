# Manuscript Template Engine — Agent Directives

## Overview

Package (`variables/`: `compute.py`, `context.py`, `formatters.py`, `inject.py`, `io.py`,
`registry.py`, `extractors/`) that reads all pipeline output JSONs and produces a complete
`dict[str, str]` of template variables. Called by `scripts/05_inject_variables.py`.

## Invariants Agents Must Preserve

- **Always multiply by 100 for percentages**: `CAGR_PCT` = `cagr * 100`. The raw `cagr` from
  `temporal_analysis.json` is a decimal fraction (e.g., 0.1699 for 16.99%). Never output
  the fraction directly as CAGR_PCT — it would render as "0.17%" in the manuscript.
- **H1–H8 aliases are order-dependent**: The mapping from config keys such as H1/H2 to scorer IDs must match `knowledge_graph.hypothesis.config_key_to_hypothesis_id`. If hypothesis key mapping changes, update both files together.
- **Infrastructure fallback**: The try/except import of `get_logger` is intentional. Do not
  remove it — the module must work both inside the template monorepo and standalone.
- **Silent fallback values**: When a JSON file is missing, `compute_variables` returns an
  empty string for that variable rather than raising. This means a missing file produces
  blank text in the manuscript rather than a hard failure. Always check that all expected
  JSON files exist in `output/data/` before running Stage 5.
- **LaTeX number formatting**: `_latex_number(n)` formats positive integers with `{,}` thousand
  separators for LaTeX (e.g., `2{,}795`). Negative numbers and floats are not handled — keep
  all counts non-negative.

## Adding a New Template Variable

1. Add a computation in `compute_variables()` reading from an existing JSON output file.
2. Store as a string: `variables["MY_VAR"] = f"{value}"`.
3. Place `{{MY_VAR}}` in the appropriate `manuscript/*.md` file.
4. Add a test in `tests/test_variables.py` verifying the value with a synthetic JSON file.
5. Update `README.md` variable table.

## Running Injection Manually

```bash
uv run python projects/templates/template_literature_meta_analysis/scripts/05_inject_variables.py
```

Output: `output/manuscript/*.md` — rendered copies of all manuscript files with all `{{VAR}}`
replaced. Documentation examples may contain literal token syntax; manuscript content should hydrate all real variables.

## Known Limitations

- **JSONL line counting**: `_count_jsonl_lines()` counts non-empty lines, not valid JSON objects.
  A malformed JSONL line counts as valid for corpus-size display; use corpus/nanopub deserializers for strict validation.
- **Reference deduplication**: `_count_total_references()` sums per-paper reference lists
  without cross-paper deduplication. The total represents raw reference entries, not unique cited works.
