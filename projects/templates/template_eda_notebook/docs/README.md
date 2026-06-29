# docs/ — Project Documentation

> **Operational rulebook** for the `template_eda_notebook` exemplar.

**Quick Reference:** [Agent Instructions](agent_instructions.md) | [Architecture](architecture.md) | [Testing](testing_philosophy.md) | [Rendering](rendering_pipeline.md) | [Style](style_guide.md) | [Syntax](syntax_guide.md) | [Index](AGENTS.md)

## Purpose

The `docs/` directory contains the behavioral and architectural rules that
govern modifications to the `template_eda_notebook` exemplar. The authoritative
file index lives in [`AGENTS.md`](AGENTS.md).

## Contents

| File | Purpose | Audience |
|---|---|---|
| [`agent_instructions.md`](agent_instructions.md) | Hard rules for AI agents; verification checklist | AI agents, all developers |
| [`architecture.md`](architecture.md) | Layer table, dependency direction, forbidden patterns, how-to-add-an-EDA-step | Developers |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, test-file inventory, class inventory (live counts → [`COUNTS.md`](../../../../docs/_generated/COUNTS.md)) | Developers, testers |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Manuscript → PDF flow; config.yaml controls | Content authors, developers |
| [`style_guide.md`](style_guide.md) | Code-style rules: Zero-Mock, library purity, thin orchestrator, explicit paths, type hints, error messages | Developers |
| [`syntax_guide.md`](syntax_guide.md) | Markdown links, figure label registry, citation syntax | Content authors |
| [`output_conventions.md`](output_conventions.md) | Output directory layout, what's disposable, regeneration rules | Developers |
| [`output_inventory.md`](output_inventory.md) | Pipeline artifact inventory (producer + stage) | Developers |
| [`forking_guide.md`](forking_guide.md) | Fork workflow and drift-check guidance | Developers, agents |
| [`troubleshooting.md`](troubleshooting.md) | Diagnosed failures with fix commands | Developers |
| [`quickstart.md`](quickstart.md) | Minimal run commands to first deliverable | New users |
| [`faq.md`](faq.md) | Recurring questions: architecture, testing, manuscript | All |
| [`AGENTS.md`](AGENTS.md) | Technical index of this `docs/` folder; verification commands | Developers, agents |

## Quick Navigation

### Before modifying any code

1. Read **[Agent Instructions](agent_instructions.md)** — the rules and the verification checklist.
2. Read **[Architecture](architecture.md)** — layer boundaries before touching file structure.
3. Read **[Testing Philosophy](testing_philosophy.md)** — the zero-mock constraint before writing tests.

### Before editing manuscript files

1. Read **[Rendering Pipeline](rendering_pipeline.md)**.
2. Read **[Syntax Guide](syntax_guide.md)** — figure label registry and citation syntax.

### Before writing source code

1. Read **[Style Guide](style_guide.md)**.

## Using this exemplar as a reference

`template_eda_notebook` teaches the **notebook -> tested src extraction**
workflow. Mirror these invariants — they are what the repo's gates enforce:

| Invariant | Where it's taught | How it's enforced |
|---|---|---|
| Thin orchestrator: `scripts/` + notebook cells only call `src/`; logic in `src/eda/` | [`architecture.md`](architecture.md), [`style_guide.md`](style_guide.md) | code review + `src/` infra-import scan |
| Zero mocks: real CSV / frames / `tmp_path` | [`testing_philosophy.md`](testing_philosophy.md) | `scripts/verify_no_mocks.py` |
| ≥90% project coverage on `src/` | [`testing_philosophy.md`](testing_philosophy.md) | `--cov-fail-under=90` |
| `manuscript/config.yaml` is the configuration source of truth | [`rendering_pipeline.md`](rendering_pipeline.md) | rendering infra |
| Deterministic outputs (fixed-seed CSV); everything in `output/` regeneratable | [`output_conventions.md`](output_conventions.md) | reproducibility checks |

### Fork seed

```bash
NEW=my_eda_project
uv run python scripts/copy_exemplar.py \
  --source templates/template_eda_notebook \
  --dest "projects/working/$NEW" --new-name "$NEW"
cd "projects/working/$NEW"
# 1. Replace data/measurements.csv + update src/eda/dataset.py::DatasetSchema
# 2. Extend src/eda/ with your transforms (keep them pure; no plotting/I/O)
# 3. Replace tests/ — real-data, no mocks, drive src/ coverage >= 90%
# 4. Edit manuscript/config.yaml (title, authors)
# 5. Update the notebook cells + scripts/eda_analysis.py to call your functions
uv run pytest "projects/working/$NEW/tests" --cov="projects/working/$NEW/src" --cov-fail-under=90
```

## Verification Commands

```bash
# Tests pass + coverage >= 90%
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch" projects/templates/template_eda_notebook/tests/ || echo "Clean"

# src/ has no infrastructure imports
grep -r "from infrastructure\|import infrastructure" projects/templates/template_eda_notebook/src/ || echo "Clean"
```

## See Also

- [../AGENTS.md](../AGENTS.md) — Full project documentation.
- [../README.md](../README.md) — Project quick start.
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — Manuscript directory rules and figure protocol.
- [output_conventions.md](output_conventions.md) — Output directory structure and regeneration.
