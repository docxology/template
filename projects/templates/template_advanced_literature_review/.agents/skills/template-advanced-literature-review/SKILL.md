---
name: template-advanced-literature-review
description: "Multi-phase literature-review exemplar with phase-aware retrieval, filtering, provenance, and cross-phase validation."
version: 0.1.0
author: docxology
license: CC-BY-4.0
tags: [exemplar, literature, systematic-review, multi-phase]
---

# template-advanced-literature-review

Load this project-scoped skill when working inside
`projects/templates/template_advanced_literature_review/` or forking it into a
new phased systematic review.

## When to Use

- A review requires distinct query phases or methodological eras.
- Papers must retain discovery-phase and cross-phase provenance.
- Phase-specific deterministic or optional LLM filters need validation.

## Quick Reference

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_advanced_literature_review --project-only
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_advanced_literature_review
uv run python scripts/pipeline/stage_03_render.py --project templates/template_advanced_literature_review
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_advanced_literature_review
```

## Pitfalls

- Stage 01 retrieval is live network work; the tracked corpus is an evidence snapshot.
- Keep phase logic in `src/multi_phase/` and numbered scripts thin.
- Use real local HTTP servers in tests; never introduce mock frameworks.
- Run stage 11 before stage 10 when adding full-text reproducibility evidence.
