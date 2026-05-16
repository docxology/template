# `template_prose_project/docs/`

Agent guide for the project's documentation hub.

## Purpose

Centralise human- and agent-facing documentation that goes beyond the
top-level [`README.md`](../README.md) and [`AGENTS.md`](../AGENTS.md):
behavioural constraints for AI agents, architectural diagrams, manuscript
syntax, output conventions, the four-phase rendering pipeline, the testing
philosophy, and a diagnostic flowchart for common failures.

Every document is a hard constraint, not a suggestion. AI agents must read
[`agent_instructions.md`](agent_instructions.md) before modifying any file
in this project.

## File Inventory

| File | Purpose | Lines |
|---|---|---|
| [`README.md`](README.md) | Quick navigation and audience-targeted entry points | ~70 |
| [`AGENTS.md`](AGENTS.md) | This file — technical overview of `docs/` | ~115 |
| [`agent_instructions.md`](agent_instructions.md) | 7 hard rules for AI agents (read-first priority); verification checklist | ~195 |
| [`architecture.md`](architecture.md) | Two-layer compliance + data-flow sequence diagram | 79 |
| [`style_guide.md`](style_guide.md) | 7 rules: Zero-Mock, Infrastructure Delegation, Thin Orchestrator, Show-Not-Tell, Explicit Paths, Type Hints, Error Messages | ~255 |
| [`syntax_guide.md`](syntax_guide.md) | Pandoc-crossref `[@sec:…]`, all eleven `{{TOKEN}}`s, code blocks, no-figures rationale | ~210 |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock standard; 67 tests; 100% src coverage; integration test | ~140 |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Four-phase manuscript→PDF flow; config.yaml controls; troubleshooting | ~225 |
| [`output_conventions.md`](output_conventions.md) | Producer/consumer table for every artefact in `output/` | 64 |
| [`quickstart.md`](quickstart.md) | 5-step first-run walkthrough | 81 |
| [`troubleshooting.md`](troubleshooting.md) | Diagnostic flowchart for common failures | 117 |
| [`faq.md`](faq.md) | Architecture, testing, manuscript, common pitfalls | ~220 |

## Key Conventions

**Read-first protocol.** AI agents must read `agent_instructions.md` before
modifying any project file. The seven rules cover: reading order, coverage
gate, the thin-orchestrator boundary inside `src/`, "show not tell"
documentation, determinism, the style/syntax-guide split, and the
disposability of `output/`.

**Architecture isolation.** The `src/` boundary is fine-grained for this
project. `src/pipeline.py` is the **only** module that performs
infrastructure operations (`analyze_manuscript`, `parse_bibfile`,
`write_report`); other `src/` modules may import infrastructure *types*
(`ManuscriptReport`, `render_outline`) but not call analysis or I/O
functions. See [`style_guide.md`](style_guide.md) Rule 2 for the full
delegation table.

**Zero-mock enforcement.** No `unittest.mock`, `MagicMock`, `@patch`, or
`create_autospec` anywhere in `tests/`. Tests use real Markdown, real
BibTeX, real `tmp_path` directories, and real subprocess invocation. The
suite collects 67 tests and achieves 100% line + branch coverage on `src/`.

**Show-not-tell.** Manuscript references must use explicit file paths and
function names, not vague descriptions. A reader of `02_methodology.md`
should be able to open `src/pipeline.py` and find the exact check being
discussed within ten seconds.

**Every diagram must be Mermaid.** No ASCII art (project-wide rule).

## Reading Order

This sequence is intentional. Each document provides context the next one
assumes:

1. **[`agent_instructions.md`](agent_instructions.md)** — Start here. Seven
   hard rules; the consequence of violating each; the verification checklist
   you run before submitting.
2. **[`architecture.md`](architecture.md)** — Two-layer compliance diagram
   (infrastructure → src → scripts) and the data-flow sequence diagram.
3. **[`testing_philosophy.md`](testing_philosophy.md)** — Zero-mock
   constraint, test-file inventory, coverage mechanics, and the integration
   test pattern.
4. **[`rendering_pipeline.md`](rendering_pipeline.md)** — Four phases of the
   manuscript→PDF flow; complete `config.yaml` control table; troubleshooting.
5. **[`style_guide.md`](style_guide.md)** — Seven style rules governing
   Python under `src/`, `scripts/`, `tests/`. Rule 2's delegation table is
   the most-cited reference in this project.
6. **[`syntax_guide.md`](syntax_guide.md)** — Pandoc-crossref section
   references, the eleven `{{TOKEN}}`s, and the rationale for embedding no
   figures in the manuscript.
7. **[`faq.md`](faq.md)** — Recurring questions and pitfalls.

## Verification Commands

These three commands verify the most critical constraints. Run all three
before submitting any change:

```bash
# 1. Test suite passes + coverage ≥ 90%
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-fail-under=90 -q

# 2. No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/template_prose_project/tests/ || echo "Clean"

# 3. Only pipeline.py performs infrastructure operations
grep -nE "analyze_manuscript|parse_bibfile|write_report" \
    projects/template_prose_project/src/figures.py \
    projects/template_prose_project/src/report.py \
    projects/template_prose_project/src/manuscript_variables.py \
    projects/template_prose_project/src/config.py \
    || echo "Clean"
```

## See also

* [`README.md`](README.md) — quick links.
* [`../AGENTS.md`](../AGENTS.md) — project-level agent guide.
* [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — substitution-marker registry.
* [`../src/AGENTS.md`](../src/AGENTS.md) — domain-orchestration guide.
* [`../tests/AGENTS.md`](../tests/AGENTS.md) — test-suite agent guide.
* [`../../../docs/rules/folder_structure.md`](../../../docs/rules/folder_structure.md) — repository-wide tri-doc convention.
* [`../../../infrastructure/prose/SKILL.md`](../../../infrastructure/prose/SKILL.md) — underlying analysis API.
* [`../../../infrastructure/reference/SKILL.md`](../../../infrastructure/reference/SKILL.md) — bibliography validation API.
