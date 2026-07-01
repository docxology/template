# `tests/regression/projects/template_literature_meta_analysis/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_literature_meta_analysis` go under
`tables/`. Use the `pinned_values` fixture; do not hardcode expected
numbers in test bodies.

**Offline only.** This exemplar's live pipeline makes network calls
(multi-engine retrieval). Regression tests MUST NOT hit the network:
re-derive every value from the committed deterministic seed corpus
`data/fixtures/modafinil_corpus.jsonl` via
`literature.corpus.Corpus.load`, exactly as the offline default run and
`src/manuscript/variables.py` do.

**Import isolation.** Load the project's own `src` package via the
`_load_src_package` helper in
`tables/test_field_overview_claims.py` (registers it under the
`_literature_meta_analysis_src` alias) rather than a bare
`sys.path.insert` + `from src...` import at module level — every exemplar
ships a top-level `src` package, and the bare pattern collides across
projects once more than one is collected in the same pytest session.
Because this exemplar's own modules use **absolute** imports
(`from literature.models import Paper`, `from analysis.subfield_defaults
import ...`), the helper also installs a project-scoped `sys.meta_path`
finder that resolves this exemplar's top-level `src` package names
(`literature`, `analysis`, …) from its own `src/` directory only — no
global `sys.path` entry, so it never shadows another exemplar that also
ships a top-level `analysis` package (e.g. `template_code_project`).
