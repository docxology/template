# tables/ — agent guide

One test file for the manuscript's structural counts
(`test_structure_claims.py`). Use the `pinned_values` fixture; load the
expected values from `pinned_values/template_textbook.json`. Re-derive
each count from `manuscript/config.yaml` through the tested
`textbook.config` / `textbook.toc` loaders — never hardcode the number
in the test body. Provenance discipline per
[`../../../AGENTS.md`](../../../AGENTS.md).
