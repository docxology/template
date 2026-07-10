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
- Checking cross-fond citation overlap (`check_bibliography_overlap()`) or
  proving a tool's entrypoint actually executes (not just that the file exists).

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_pools_rules_tools/tests/ \
  --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90

uv run python projects/templates/template_pools_rules_tools/scripts/01_validate_sources.py
uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
uv run python projects/templates/template_pools_rules_tools/scripts/03_generate_manuscript.py
uv run python projects/templates/template_pools_rules_tools/scripts/04_validate_strong_rules.py
uv run python projects/templates/template_pools_rules_tools/scripts/05_generate_figures.py
uv run python projects/templates/template_pools_rules_tools/scripts/z_generate_manuscript_variables.py

uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_pools_rules_tools
uv run python scripts/pipeline/stage_03_render.py --project templates/template_pools_rules_tools
uv run python scripts/runner/execute_pipeline.py --project templates/template_pools_rules_tools --core-only
```

## Pitfalls

- **Read-only resource dirs.** Never mutate `fonds/`, `rules/`, or `tools/` from project `src/`.
- **No infrastructure imports in `src/`.** Scripts orchestrate; readers stay standalone-friendly.
- **No mocks.** Tests use real template paths, temp dirs, or `pytest.mark.skipif` when files are absent.
- **Outputs are disposable.** Regenerate `output/` via pipeline stages; do not hand-edit copied deliverables.
- **Repo root resolution.** `src/*` resolves the monorepo root four levels above each module file.
- **`manuscript/preamble.md` needs a closed ` ```latex ``` ` fence.** An unfenced file silently drops every multi-line directive (geometry, hypersetup, tcolorbox) via a whitelist fallback — only single-line `\usepackage{}`/`\newcommand{}` survive. Always verify with `extract_preamble()` after editing.
- **Manuscript tokens must be `{{UPPERCASE_KEY}}`, never lowercase-dotted.** `infrastructure/rendering/manuscript_injection.py`'s regex only matches uppercase; a `{{integration.foo}}`-style token silently never resolves. The pipeline also requires `scripts/z_generate_manuscript_variables.py` to exist by that exact name — `run_manuscript_variable_script()` no-ops if it's absent.
- **`config.yaml`'s `figures:` registry is metadata only.** It does not auto-insert images — every figure needs a real `![caption](figures/x.png){#fig:label}` block in the manuscript body, or its `@fig:` cross-reference renders as a literal `??`.
- **Custom tcolorbox environments (`noteBox`/`warningBox`) break Beamer slide generation** even though they render fine in the combined PDF — pandoc's per-section slide splitting can separate `\begin`/`\end` across frame boundaries. Prefer plain Markdown emphasis for callouts.
- **`run.sh`/`validate.sh` subprocess tests are real but environment-guarded.** `timeout`/`gtimeout` are absent on stock macOS — the code-executor tests skip there by design; don't "fix" a SKIPPED result by removing the skipif guard.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Fonds layer: [`fonds/AGENTS.md`](../../../../../../fonds/AGENTS.md)
- Rules layer: [`rules/AGENTS.md`](../../../../../../rules/AGENTS.md)
- Tools layer: [`tools/AGENTS.md`](../../../../../../tools/AGENTS.md)
