# docs/ — Project Documentation

> **Operational rulebook** for the `template_methods_paper` exemplar.

**Quick Reference:** [Agent Instructions](agent_instructions.md) | [Architecture](architecture.md) | [Testing](testing_philosophy.md) | [Rendering](rendering_pipeline.md) | [Style](style_guide.md) | [Syntax](syntax_guide.md) | [Index](AGENTS.md)

## Purpose

The `docs/` directory contains the behavioral and architectural rules that
govern modifications to the `template_methods_paper` exemplar. The authoritative
file index lives in [`AGENTS.md`](AGENTS.md).

## Contents

| File | Purpose | Audience |
|---|---|---|
| [`agent_instructions.md`](agent_instructions.md) | Hard rules for AI agents; verification checklist | AI agents, all developers |
| [`architecture.md`](architecture.md) | Layer table, dependency direction, forbidden patterns, how-to-add-a-method | Developers |
| [`testing_philosophy.md`](testing_philosophy.md) | Zero-mock policy, test-file inventory (live counts → [`COUNTS.md`](../../../../docs/_generated/COUNTS.md)) | Developers, testers |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Manuscript → PDF flow; `{{TOKEN}}` controls | Content authors, developers |
| [`style_guide.md`](style_guide.md) | Code-style rules: zero-mock, library purity, thin orchestrator, explicit paths, type hints, error messages | Developers |
| [`syntax_guide.md`](syntax_guide.md) | Markdown links, figure/table label registry, citation syntax, `{{TOKEN}}` reference | Content authors |
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
2. Read **[Syntax Guide](syntax_guide.md)** — `{{TOKEN}}` and figure label registry.

### Before writing source code

1. Read **[Style Guide](style_guide.md)**.

## Using this exemplar as a reference

`template_methods_paper` teaches the **controlled-vocabulary-in-code, not a
parser** approach to a methods paper. Mirror these invariants — they are
what the repo's gates enforce:

| Invariant | Where it's taught | How it's enforced |
|---|---|---|
| Thin orchestrator: `scripts/` only calls `src/`; gate/compile logic stays in `src/methods_dsl/` | [`architecture.md`](architecture.md), [`style_guide.md`](style_guide.md) | code review + `src/methods_dsl/` infra-import scan |
| Zero mocks: real `Method` fixtures / `tmp_path` | [`testing_philosophy.md`](testing_philosophy.md) | `scripts/audit/verify_no_mocks.py` |
| ≥90% project coverage on `src/` | [`testing_philosophy.md`](testing_philosophy.md) | `--cov-fail-under=90` |
| `manuscript/config.yaml` is the configuration source of truth | [`rendering_pipeline.md`](rendering_pipeline.md) | rendering infra |
| Deterministic outputs (stable `plan_hash`); everything in `output/` regeneratable | [`output_conventions.md`](output_conventions.md) | reproducibility checks |

### Fork seed

```bash
NEW=my_methods_project
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_methods_paper \
  --dest "projects/working/$NEW" --new-name "$NEW"
cd "projects/working/$NEW"
# 1. Replace src/methods_dsl/examples_methods.py with your own Method(s)
# 2. Extend src/methods_dsl/vocabulary.py / units.py only if your domain needs
#    a new StepKind / Dimension (keep additions in the controlled vocabulary)
# 3. Replace tests/ — real Method fixtures, no mocks, drive src/ coverage >= 90%
# 4. Edit manuscript/config.yaml (title, authors)
# 5. Update scripts/methods_analysis.py to compile your method(s)
uv run pytest "projects/working/$NEW/tests" --cov="projects/working/$NEW/src" --cov-fail-under=90
```

## Verification Commands

```bash
# Tests pass + coverage >= 90%
uv run pytest projects/templates/template_methods_paper/tests \
    --cov=projects/templates/template_methods_paper/src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch" projects/templates/template_methods_paper/tests/ || echo "Clean"

# src/methods_dsl/ has no unsanctioned infrastructure imports
grep -rnE "^(from|import) infrastructure" projects/templates/template_methods_paper/src/methods_dsl/ \
    | grep -v "_logging.py" || echo "Clean"
```

## See Also

- [../AGENTS.md](../AGENTS.md) — Full project documentation.
- [../README.md](../README.md) — Project quick start.
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — Manuscript directory rules and token/figure protocol.
- [output_conventions.md](output_conventions.md) — Output directory structure and regeneration.
