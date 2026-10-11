# `tests/regression/projects/template_literature_meta_analysis/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_literature_meta_analysis` go under
`tables/`. Use the `pinned_values` fixture; do not hardcode expected
numbers in test bodies.

**Offline only.** This exemplar's live pipeline makes network calls
(multi-engine retrieval). Regression tests MUST NOT hit the network:
re-derive every value from the committed deterministic seed corpus
`data/fixtures/modafinil_corpus.jsonl` via
`template_literature_meta_analysis.literature.corpus.Corpus.load`, exactly as the offline default run and
`src/manuscript/variables.py` do.

**Import isolation.** Use the canonical source registration in
`tables/test_field_overview_claims.py`. It admits
`template_literature_meta_analysis` and its cached descendants only from the
exact exemplar source tree. Use canonical qualified imports; keep generic
sibling names, global search paths, and process-wide import finders untouched.
The source-origin and sibling-shadow controls live in
`tests/infra_tests/regression/test_literature_source_imports.py`.
