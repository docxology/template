# `tests/regression/projects/template_search_project/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

`template_search_project` is the literature-search → BibTeX →
LLM-synthesis exemplar. Its live pipeline can fan out to arXiv /
Crossref over the network, so the regression tier binds **only** to
the offline default: the committed deterministic corpus
[`data/corpus.json`](../../../../projects/templates/template_search_project/data/corpus.json)
(6 curated papers, `sources: [local]`). Every pinned value is
re-derived by calling the real source functions the manuscript
pipeline uses — never the network, never a hand-copied manuscript
number:

- `{{RESULT_NUM_PAPERS}}` / `{{RESULT_WITH_DOI}}` /
  `{{RESULT_WITH_ABSTRACT}}` — via
  `infrastructure.search.literature.LiteratureClient.search` over a
  `LocalBackend` and `src.manuscript_variables.compute_variables`.
- BibTeX entry count + collision-free citation keys — via
  `src.pipeline._build_citation_keys`.

## Import isolation (meta_path finder, NOT the plain alias)

Every public exemplar ships a top-level `src` package, so a bare
`sys.path.insert` + `from src...` collides on `sys.modules['src']`
once a second project's regression test joins the same pytest
session. Unlike `template_prose_project` (whose `manuscript_variables`
uses only *relative* imports and so loads cleanly under a plain
project-unique alias), **this** exemplar's
`src/manuscript_variables.py` does `from src.config import
DeepSearchConfig` — an *absolute* `src.` import that `src/__init__.py`
imports eagerly. So the plain-alias pattern fails at package load with
`ModuleNotFoundError: No module named 'src'`. The test therefore
installs a project-scoped `sys.meta_path` finder (like
`template_literature_meta_analysis`) that resolves the bare `src` name
to *this* project's `src/` directory only — never a global
`sys.path` entry — so the absolute import resolves without shadowing
another exemplar's top-level packages (`analysis`, `config`, …).

Provenance discipline per [`../../pinned_values/AGENTS.md`](../../pinned_values/AGENTS.md).
