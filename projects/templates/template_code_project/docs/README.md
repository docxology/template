# docs/ — Project Documentation

> **Operational rulebook** for the template_code_project exemplar

**Quick Reference:** [Agent Instructions](agent_instructions.md) | [Architecture](architecture.md) | [Testing](testing_philosophy.md) | [Rendering](rendering_pipeline.md) | [Style](style_guide.md) | [Syntax](syntax_guide.md) | [Index](AGENTS.md)

## Purpose

The `docs/` directory contains the behavioral and architectural rules that govern modifications to the `template_code_project` exemplar. Every document here is a hard constraint — not a suggestion. The authoritative file index (including this `README.md` and `AGENTS.md`) lives in [`AGENTS.md`](AGENTS.md).

## Contents

| File | Purpose | Audience |
|---|---|---|
| [`agent_instructions.md`](agent_instructions.md) | 7 hard rules for AI agents; verification checklist | AI agents, all developers |
| [`architecture.md`](architecture.md) | Layer table, dependency direction, forbidden patterns, how-to-add-algorithm | Developers |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, test-file inventory, coverage mechanics, the gate-vs-exit-code rule (live counts → [`canonical_facts.md`](../../../../docs/_generated/canonical_facts.md)) | Developers, testers |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Mermaid/chrome prerequisite; 4-phase manuscript→PDF pipeline; config.yaml controls | Content authors, developers |
| [`style_guide.md`](style_guide.md) | 7 rules: Zero-Mock, Infrastructure Delegation, Thin Orchestrator, Show-Not-Tell, Explicit Paths, Type Hints, Error Messages | Developers |
| [`syntax_guide.md`](syntax_guide.md) | Markdown links, LaTeX refs, all `{{VARIABLE}}` tokens, figure label registry | Content authors |
| [`output_conventions.md`](output_conventions.md) | Output directory layout, what's disposable, regeneration rules | Developers |
| [`output_inventory.md`](output_inventory.md) | Full pipeline artifact inventory (generator + stage) | Developers |
| [`forking_guide.md`](forking_guide.md) | Fork workflow and drift-check guidance | Developers, agents |
| [`troubleshooting.md`](troubleshooting.md) | Diagnosed failures incl. `mmdc`/Chrome and "PASSED but 0 tests", with fix commands | Developers |
| [`quickstart.md`](quickstart.md) | Minimal run commands to first deliverable | New users |
| [`faq.md`](faq.md) | Recurring questions: architecture, testing, manuscript | All |
| [`AGENTS.md`](AGENTS.md) | Technical index of this `docs/` folder; verification commands | Developers, agents |

## Quick Navigation

### Before Modifying Any Code

1. Read **[Agent Instructions](agent_instructions.md)** — 7 rules and the verification checklist
2. Read **[Architecture](architecture.md)** — understand layer boundaries before touching file structure
3. Read **[Testing Philosophy](testing_philosophy.md)** — understand zero-mock constraint before writing tests

### Before Editing Manuscript Files

1. Read **[Rendering Pipeline](rendering_pipeline.md)** — understand the 4-phase pipeline
2. Read **[Syntax Guide](syntax_guide.md)** — complete `{{VARIABLE}}` token list and figure label registry

### Before Writing Source Code

1. Read **[Style Guide](style_guide.md)** — 7 rules covering mocks, imports, error messages, type hints

## Using this exemplar as a reference for a new project

`template_code_project` is a **canonical, always-present reference** (see the
root `CLAUDE.md`/`AGENTS.md`). Other projects and docs are told to default
their path/layout examples here. Use it two ways:

**1. As a pattern reference (don't copy — read).** When building any
project, mirror these invariants — they are what the repo's gates enforce:

| Invariant | Where it's taught | How it's enforced |
|---|---|---|
| Thin-orchestrator: `scripts/` only I/O + orchestration, logic in `src/`/`infrastructure/` | [`architecture.md`](architecture.md), [`style_guide.md`](style_guide.md) | code review + `src/` infra-import grep |
| Zero mocks: real data, `tmp_path`, `pytest-httpserver` | [`testing_philosophy.md`](testing_philosophy.md) | `scripts/verify_no_mocks.py` |
| ≥90% project coverage on `src/` | [`testing_philosophy.md`](testing_philosophy.md) | `--cov-fail-under=90` (canonical command below) |
| `manuscript/config.yaml` is the single source of run policy | [`rendering_pipeline.md`](rendering_pipeline.md) | rendering infra |
| Deterministic outputs (fixed seeds); everything in `output/` regeneratable | [`output_conventions.md`](output_conventions.md) | reproducibility checks |

**2. As a fork seed for a new project.** Minimum viable steps:

```bash
NEW=my_project
cp -r projects/template_code_project projects/$NEW
cd projects/$NEW
# 1. Rewrite src/ with your domain logic (keep the pure-function, infra-free shape)
# 2. Replace tests/ — real-data tests, no mocks, drive src/ coverage ≥90%
# 3. Edit manuscript/config.yaml (title, authors, thresholds) — the only policy knob
# 4. Replace manuscript/*.md with your narrative; keep {{TOKEN}} + figure-label conventions
# 5. Point scripts/ at your src/ functions (thin orchestrators only)
uv run pytest projects/$NEW/tests/ --cov=projects/$NEW/src --cov-fail-under=90
uv run python scripts/execute_pipeline.py --project $NEW --core-only
```

Then the project is discovered automatically (`discover_projects()`); the
repo-level guide [`docs/guides/new-project-setup.md`](../../../../docs/guides/new-project-setup.md)
covers the full workflow.

**Prerequisites to know before referencing the render path:** combined-PDF
rendering of any ```mermaid``` block needs `chrome-headless-shell`
(`npx --yes puppeteer browsers install chrome-headless-shell`); the per-project
test gate is the **direct** command below (a green `01_run_tests.py` exit with
0 collected tests is not a pass). Both are detailed in
[`troubleshooting.md`](troubleshooting.md) and [`rendering_pipeline.md`](rendering_pipeline.md).

**Code vs. prose — pick the right reference.** Use **`template_code_project`**
when the deliverable is computed (algorithms, figures from data, numerical
results). Use the sibling **[`template_prose_project`](../../template_prose_project/)**
when the deliverable is editorial (readability/structure/citation review of
written prose). Both share the identical structural contract above; they
differ only in what `src/` computes and what the pipeline checks.

## Verification Commands

```bash
# Tests pass + coverage ≥90%
uv run pytest projects/template_code_project/tests/ \
    --cov=projects/template_code_project/src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch" projects/template_code_project/tests/ || echo "Clean"

# src/ has no infrastructure imports
grep -r "from infrastructure\|import infrastructure" projects/template_code_project/src/ || echo "Clean"
```

## See Also

- [../AGENTS.md](../AGENTS.md) — Full project documentation (API reference, known issues, complete directory map)
- [../README.md](../README.md) — Project quick start
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — Manuscript directory rules and `{{VARIABLE}}` protocol
- [output_conventions.md](output_conventions.md) — Output directory structure and regeneration
- [../../../docs/](../../../../docs/) — Repository-level documentation hub (127 files, 14 subdirectories)
