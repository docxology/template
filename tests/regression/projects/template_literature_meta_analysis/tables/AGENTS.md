# tables/ — agent guide

One test file per manuscript results group (currently
`test_field_overview_claims.py`). Use the `pinned_values` fixture; load
values from the per-key entries in
`../../../pinned_values/template_literature_meta_analysis.json`. Re-derive
every number offline from `data/fixtures/modafinil_corpus.jsonl` via the
real source functions — never hit the network, never hand-copy a manuscript
number. Provenance discipline per
[`../../../AGENTS.md`](../../../AGENTS.md).
