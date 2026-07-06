## Results

### Grammar product space

{{SLOT_TABLE}}

- **Total product size**: {{PRODUCT_SIZE}} cells
- **Effective product size** (reserved slots excluded): {{EFFECTIVE_PRODUCT_SIZE}} cells
- **Reserved slots** ({{RESERVED_SLOT_COUNT}}): `{{RESERVED_SLOT_NAMES}}`

### Effective slot breakdown

{{EFFECTIVE_SLOT_TABLE}}

### Exemplar generation

Running `uv run python scripts/autopoiesis.py expand --seed 42` produces a spec
with `primitive_domain` deterministically selected from the grammar.

All {{DOMAIN_COUNT}} domains successfully materialize runnable child projects.
Each child project:

1. Contains a `primitives/` package with the selected kernel.
2. Runs `analysis.py` without error.
3. Has a `provenance.json` that passes `verify_child`.
4. Passes all child-level smoke tests.

### Test results

- **Test count**: {{TEST_COUNT}}
- **Coverage**: {{COVERAGE_PCT}}%
- **Grammar hash**: `{{GRAMMAR_HASH}}`
