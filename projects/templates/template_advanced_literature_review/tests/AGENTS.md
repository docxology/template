# Tests — Agent Directives

Exercise the advanced exemplar's project-owned phase/configuration behavior with
real data structures, temporary files, and local HTTP servers. Do not use
`unittest.mock`, `MagicMock`, `mocker.patch`, or call-count-only assertions.

Keep tests hermetic: no external search engine or LLM access. Assertions should
prove filtering boundaries, phase provenance, cross-phase relationships,
configuration validation, and output-path containment.

The project-local 90% coverage gate measures `src/multi_phase/`. Shared
literature, config-validation, and manuscript-variable modules are inherited
from `template_literature_meta_analysis` and remain covered by that exemplar's
own complete suite.
