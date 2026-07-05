# Usage Guides Documentation

## Overview

Technical guide for `docs/guides/` — skill-level progression guides from beginner to expert.

## Files

| File | Skill Levels | Audience |
|------|-------------|----------|
| `startup-and-setup.md` | Levels 1-3 | Copy-pasteable install + validation procedure (humans and agents) |
| `getting-started.md` | Levels 1-3 | New users and content creators |
| `figures-and-analysis.md` | Levels 4-6 | Researchers adding figures and automation |
| `testing-and-reproducibility.md` | Levels 7-9 | Developers implementing TDD workflow |
| `extending-and-automation.md` | Levels 10-12 | Expert users extending the template |
| `new-project-setup.md` | All levels | Complete setup checklist with pitfalls |
| `new-project-one-shot-prompt.md` | All levels | LLM one-shot scaffold; primary exemplar `projects/templates/template_code_project/`; active names in `_generated/active_projects.md` |
| `methods-orchestration.md` | Advanced | Methods-to-pipeline provenance and validation |
| `codegraph-local.md` | Advanced | Optional local CodeGraph index with public/private scope guards |
| `leann-local.md` | Advanced | Optional local LEANN semantic retrieval with generated-index guards |
| `llm-integration-guide.md` | Levels 11-12 | AI-assisted research: Ollama setup, LLM review, templates, programmatic usage |
| `publishing-guide.md` | Levels 11-12 | Academic publishing: DOI, Zenodo, arXiv, citations (BibTeX CLI; APA/MLA helpers) |
| `secure-research-guide.md` | Level 11 | PDF steganography: watermarks, QR codes, SHA-256 hashing, provenance |
| `zenodo-doi-strategy.md` | Levels 11-12 | Concept vs version DOI strategy for repeat Zenodo releases |
| `fork-an-exemplar.md` | All levels | Fork-readiness walkthrough for canonical exemplars |
| `literature-workflow-guide.md` | Levels 7-12 | Literature search → references workflow |
| `manuscript-semantics.md` | All levels | Canonical manuscript semantics & syntax |

## Key Conventions

- **Paths in examples**: [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/) as control-positive; other active workspaces → [_generated/active_projects.md](../_generated/active_projects.md).
- CodeGraph examples must keep `.codegraph/` local-only and verify that private symlinked projects are absent from the template-root index.
- LEANN examples must keep `.leann/` local-only, build from tracked public files or canonical private checkouts, and never treat semantic-search output as manuscript evidence.
- Guides follow a progressive skill-level structure (1-12)
- Each guide builds on the previous — prerequisites are clearly stated
- All code examples use real, working commands (no placeholders)
- Each guide ends with "Next Steps" linking to the next level

## See Also

- [README.md](README.md) — Quick navigation
- [How To Use](../core/how-to-use.md) — Comprehensive usage guide (all 12 levels)
- [Common Workflows](../reference/common-workflows.md) — Step-by-step recipes
