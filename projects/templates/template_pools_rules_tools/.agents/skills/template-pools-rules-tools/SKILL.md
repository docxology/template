---
name: template-pools-rules-tools
description: Fonds, rules, and tools integration exemplar — read resource pools, apply governance rules, validate tool manifests, and run combined integration.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, fonds, rules, tools, integration, meta-project]
---

# template-pools-rules-tools

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_pools_rules_tools/`. Load this when wiring or
validating the three-resource architecture (fonds, rules, tools).

## When to Use

- Demonstrating how a research project reads from `fonds/templates/`,
  `rules/templates/`, and `tools/templates/` without writing back to those trees.
- Validating new fond, rule, or tool exemplars through the integration pipeline.
- Onboarding agents to graceful-degradation readers (`None`/empty + logged warnings).
- Extending the meta-manuscript with integration counts and status dashboards.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_pools_rules_tools/tests/ \
  --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90

uv run python projects/templates/template_pools_rules_tools/scripts/01_validate_sources.py
uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
uv run python projects/templates/template_pools_rules_tools/scripts/03_generate_manuscript.py

uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_pools_rules_tools
uv run python scripts/pipeline/stage_03_render.py --project templates/template_pools_rules_tools
```

## Pitfalls

- **Read-only resource dirs.** Never mutate `fonds/`, `rules/`, or `tools/` from project `src/`.
- **No infrastructure imports in `src/`.** Scripts orchestrate; readers stay standalone-friendly.
- **No mocks.** Tests use real template paths, temp dirs, or `pytest.mark.skipif` when files are absent.
- **Outputs are disposable.** Regenerate `output/` via pipeline stages; do not hand-edit copied deliverables.
- **Repo root resolution.** `src/*` resolves the monorepo root four levels above each module file.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Fonds layer: [`fonds/AGENTS.md`](../../../../../../fonds/AGENTS.md)
- Rules layer: [`rules/AGENTS.md`](../../../../../../rules/AGENTS.md)
- Tools layer: [`tools/AGENTS.md`](../../../../../../tools/AGENTS.md)
