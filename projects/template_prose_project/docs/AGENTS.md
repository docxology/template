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
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock standard; coverage mechanics; integration test (live counts in `docs/_generated/canonical_facts.md`) | ~140 |
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
BibTeX, real `tmp_path` directories, and real subprocess invocation. Live
test count and achieved coverage are tracked in
[`canonical_facts.md`](../../../docs/_generated/canonical_facts.md); the
suite runs well above the 90% gate.

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

## REQUIRED vs AESTHETIC

A forker copying this exemplar should know which directories and files
are pipeline-enforced (delete them and the gate fails) and which are
convention only (delete them and nothing complains automatically). The
distinction matters when you trim the template down to your minimum
viable project.

| Path | Status | Enforcing gate / source of truth |
|------|--------|---------------------------------|
| `src/pipeline.py` | REQUIRED | Coverage gate; every `_check_<name>` is exercised by `tests/test_pipeline.py` |
| `src/config.py` | REQUIRED | `tests/test_config.py` |
| `src/figures.py` | REQUIRED | `tests/test_figures.py` |
| `src/manuscript_variables.py` | REQUIRED | `tests/test_manuscript_variables.py` + the live `{{TOKEN}}` cross-reference test |
| `src/report.py` | REQUIRED | `tests/test_report.py` |
| `tests/` (all `test_*.py`) | REQUIRED | 90% coverage gate (per-project and root pipeline) |
| `tests/conftest.py` | REQUIRED | Pinning `MPLBACKEND=Agg` is load-bearing for CI |
| `scripts/run_prose_pipeline.py` | REQUIRED | `tests/test_scripts.py` exercises via subprocess |
| `scripts/y_generate_prose_figures.py` | REQUIRED | `tests/test_scripts.py` (after Tier M: subprocess test with `--project-root`) |
| `scripts/z_generate_manuscript_variables.py` | REQUIRED | `tests/test_scripts.py` (after Tier M: dedicated subprocess test) |
| `scripts/00_preflight.py` | AESTHETIC | Emits a warning before PDF render; pipeline still runs without it |
| `manuscript/config.yaml` | REQUIRED | `src/config.py` loader; pipeline aborts without it |
| `manuscript/*.md` | REQUIRED | Read by `infrastructure.prose.analyze_manuscript`; no manuscript = no run |
| `manuscript/references.bib` | REQUIRED | `_check_bibliography` reads it; `fail_on_missing=true` blocks empty bib |
| `manuscript/preamble.md` | REQUIRED | Injected at PDF compile; missing → LaTeX errors |
| `manuscript/SYNTAX.md` | AESTHETIC | Authoring guide for humans; pipeline never reads it |
| `manuscript/config.yaml.example` | AESTHETIC | Documentation; forkers copy → `config.yaml` |
| `manuscript/AGENTS.md` | AESTHETIC | Agent guide; pipeline never reads it (and the substitution pass deliberately skips it) |
| `docs/*.md` | AESTHETIC | Agent + human documentation; no gate parses these |
| `docs/style_guide.md`, `docs/agent_instructions.md`, etc. | AESTHETIC (load-bearing for *agents*, not pipelines) | Drift detected only by audits; aspire to convert to a gate (see TIER L proposal `scripts/check_template_drift.py`) |
| `src/STYLE.md`, `tests/PATTERNS.md`, `scripts/CONVENTIONS.md` | AESTHETIC | Sibling-parity files; no automated enforcement |
| `src/AGENTS.md`, `tests/AGENTS.md`, `scripts/AGENTS.md` | AESTHETIC | Per-subdir agent guides |
| `pyproject.toml` | REQUIRED | Coverage gate config, pytest options, dependency declarations |
| `.gitignore` | REQUIRED | Public-repo confidentiality invariant (see root `CLAUDE.md`) |
| `README.md`, `AGENTS.md` (root) | AESTHETIC (load-bearing for humans/agents) | Read by every newcomer; drift = a confused forker |

"AESTHETIC" does NOT mean "throwaway" — drift in an aesthetic file
typically rots over months and silently misleads future contributors. It
means "no pre-commit hook will tell you when it rots." Treat the
AESTHETIC list as the audit surface that lives outside automated CI.

## See also

* [`README.md`](README.md) — quick links.
* [`../AGENTS.md`](../AGENTS.md) — project-level agent guide.
* [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — substitution-marker registry.
* [`../src/AGENTS.md`](../src/AGENTS.md) — domain-orchestration guide.
* [`../tests/AGENTS.md`](../tests/AGENTS.md) — test-suite agent guide.
* [`../../../docs/rules/folder_structure.md`](../../../docs/rules/folder_structure.md) — repository-wide tri-doc convention.
* [`../../../infrastructure/prose/SKILL.md`](../../../infrastructure/prose/SKILL.md) — underlying analysis API.
* [`../../../infrastructure/reference/SKILL.md`](../../../infrastructure/reference/SKILL.md) — bibliography validation API.
