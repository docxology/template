---
name: Advanced Literature Manuscript Injection
description: Phase-aware tooling for injecting advanced-review evidence and statistics into Markdown manuscript templates.
---

# Instructions

You are interacting with the `src/manuscript/` templater module. This pipeline binds phase-aware retrieval evidence and computed statistical aggregates into the final LaTeX/Markdown scientific deliverables.

## Agentic Interface (MCP Strategy)

1. **Jinja2 Enforcement**: Treat `{{VAR_NAME}}` tokens cautiously. Verify your dictionary payload completely matches the requested keys inside `03_results_hypothesis.md`, etc.
2. **Immutable Upstream Constraint**: This module consumes final artifacts. Never manipulate or 'clean' the statistical values inside the injection workflow.
3. **Configurable Frontmatter**: Guarantee that the author metadata and DOI headers correctly pipe through from `manuscript/config.yaml`.
