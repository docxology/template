# template_search_project/docs

Human-facing notes and AI-agent rulebook for this exemplar. For shared literature-search references, see the repo hub [`docs/modules/literature-search-and-references.md`](../../../../docs/modules/literature-search-and-references.md) and [`docs/guides/literature-workflow-guide.md`](../../../../docs/guides/literature-workflow-guide.md).

## Quick Index

| Doc | Use when |
|---|---|
| [agent_instructions.md](agent_instructions.md) | First read for AI agents — 7 hard rules + verification checklist |
| [architecture.md](architecture.md) | Understanding module boundaries and the data-flow graph |
| [testing_philosophy.md](testing_philosophy.md) | Writing or modifying any test (zero-mock + LLM-as-callable) |
| [rendering_pipeline.md](rendering_pipeline.md) | Editing manuscript or output paths; the 5-phase flow |
| [style_guide.md](style_guide.md) | Editing `src/`, `tests/`, or `scripts/` (7 style rules) |
| [syntax_guide.md](syntax_guide.md) | Editing `manuscript/*.md` — `{{TOKEN}}` registry, figure labels, two-bib rule |
| [faq.md](faq.md) | Design rationale and common-pitfall answers |
| [quickstart.md](quickstart.md) | First run / copy-paste commands (six-step flow) |
| [architecture.md](architecture.md) | Two-layer compliance and idempotency contract |
| [output_conventions.md](output_conventions.md) | Interpreting `output/*` artifacts |
| [troubleshooting.md](troubleshooting.md) | Fixing a failed run |
| [AGENTS.md](AGENTS.md) | Index, reading order, and verification commands |

## Reading Order

For new agents:

1. [agent_instructions.md](agent_instructions.md)
2. [architecture.md](architecture.md)
3. [testing_philosophy.md](testing_philosophy.md)
4. [rendering_pipeline.md](rendering_pipeline.md)
5. [style_guide.md](style_guide.md)
6. [syntax_guide.md](syntax_guide.md)
7. [faq.md](faq.md)

For first-time contributors who just want to run the pipeline: start with [quickstart.md](quickstart.md), then jump to [troubleshooting.md](troubleshooting.md) when something breaks.
