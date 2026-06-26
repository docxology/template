# Troubleshooting

## Common errors

### "Analysis outputs required but missing"

```
FileNotFoundError: Analysis outputs required but missing: .../refinery_results.json
```

**Fix:** Run the analysis first:
```bash
uv run python scripts/refinement_analysis.py
```

Or use draft mode:
```bash
uv run python scripts/z_generate_manuscript_variables.py --allow-draft
```

### "Purity must increase monotonically"

```
ValueError: Purity must increase monotonically: stage 0 = 0.5, stage 1 = 0.3
```

**Fix:** Stage purity values in `src/refinery.py` must be strictly increasing.
Check `CANONICAL_STAGES` and ensure each `output_purity > input_purity`.

### "lexicon category 'X' must be a non-empty list"

```
GoldRefinementConfigError: lexicon category 'metallurgical_terms' must be a non-empty list
```

**Fix:** Add vocabulary to `manuscript/config.yaml` under
`gold_refinement.lexicon`. Required categories:
`metallurgical_terms`, `manuscript_terms`, `purity_adjectives`,
`refinement_verbs`.

### "Manuscript tokens not produced"

```
AssertionError: Manuscript tokens not produced by generate_variables()
```

**Fix:** A `{{TOKEN}}` in a manuscript file has no corresponding variable.
Add the variable in `src/manuscript_variables.py` or fix the token name
in the manuscript source.

### "slot category 'X' not found in lexicon"

**Fix:** The slot references a category not defined in `gold_refinement.lexicon`.
Add the category or fix the slot's `category` field.

### Matplotlib backend issues

**Fix:** Ensure `MPLBACKEND=Agg` is set (conftest.py does this for tests).
For scripts, `src/figures.py` calls `matplotlib.use("Agg")` before pyplot import.
