# tables/ — agent guide

One test file per manuscript claim group (currently
`test_layout_statistics_claims.py`). Use the `pinned_values`
fixture; load values from the top-level keys in
`../../pinned_values/template_newspaper.json`. Provenance discipline
per [`../../../AGENTS.md`](../../../AGENTS.md).

Every value is re-derived from the project's `src` via the
`_newspaper_src`-aliased loader — never hand-copied from the
manuscript or the claim ledger. The figure-count pin runs the real
`figures.generate_all` into a `tmp_path` (real Pillow/Matplotlib
output, no mocks).
