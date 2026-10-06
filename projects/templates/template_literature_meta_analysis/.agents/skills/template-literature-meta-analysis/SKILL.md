---
name: template-literature-meta-analysis
description: "Literature meta-analysis exemplar — multi-engine retrieval, dedup, full-text, bibliometrics, embeddings, optional knowledge graph. Default term: modafinil."
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, literature, meta-analysis, bibliometrics]
---

# template-literature-meta-analysis

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_literature_meta_analysis/`. Load this when working inside the project.

## When to Use

- Working inside the `template_literature_meta_analysis` exemplar — running scripts, editing source,
  or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new research project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
# Canonical fresh-clone gate: provisions the project's isolated dependencies.
uv run python scripts/pipeline/stage_01_test.py --project templates/template_literature_meta_analysis --project-only
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_literature_meta_analysis
uv run python scripts/pipeline/stage_03_render.py --project templates/template_literature_meta_analysis
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_literature_meta_analysis
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_literature_meta_analysis
```

For an independent source checkout, first prepare its own environment with the
actual platform 4.0.0 wheel and this project's `dev` extra as described in
[`STANDALONE.md`](../../../STANDALONE.md). These candidates are unreleased;
do not assume they are available from a package index. Run from the standalone
checkout's root:

```bash
python -I -m pytest tests/ --cov=src --cov-fail-under=90
```

The standalone command uses its own `pyproject.toml`; it requires no Root-stage
script. The Stage-01 command above provisions dependencies for monorepo work.

## Pitfalls

- **Keep scripts thin.** Business logic belongs in `src/` or shared
  `infrastructure/`, not in `scripts/`.
- **No mocks.** All tests must use real data, real files, and real
  computation.
- **Select the documented command for the checkout.** Use Stage 01 from the
  monorepo root, or the configured pytest command from the prepared standalone
  environment. Both require this exemplar's declared scientific dependencies.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  source and config.
- **Use the correct working directory.** Stage commands run from the monorepo
  root; standalone pytest runs from the exemplar root.

## Optional gap-filler search (Monid)

Use MCP connectors and configured retrieval keys first. For uncovered endpoints,
Monid (`infrastructure/search/monid/`) is infrastructure-only — pricing table:
[`PRICING.md`](../../../../../infrastructure/search/monid/PRICING.md). Offline
`deep_research` replay (`scripts/08_deep_research_dispatch.py`) remains the
exemplar's default long-form synthesis path.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../../AGENTS.md)
