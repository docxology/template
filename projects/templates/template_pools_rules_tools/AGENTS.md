# AGENTS.md — template_pools_rules_tools

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md).

Meta-project demonstrating fonds, tools, and rules integration. Public exemplar
in `projects/templates/`. Nearest-child `AGENTS.md` files take precedence
for directory-specific rules.

---

## Purpose

Ground truth for integration counts lives in `output/data/manuscript_variables.json`;
configuration is owned by `manuscript/config.yaml`.

This exemplar shows how a project reads from the three top-level resource
directories:

- **`fonds/templates/`** — passive data pools (bibliography, contacts, datasets)
- **`rules/templates/`** — governance rule sets (soft guidelines + strong schemas)
- **`tools/templates/`** — executable tool entry points

All resource directories are read-only from this project's perspective. Never
write back to `fonds/`, `rules/`, or `tools/` from project code.

---

## Layer Contract

| Surface | Rule |
|---|---|
| `src/` | Pure readers and validators — no `infrastructure` imports |
| `scripts/` | Thin orchestrators; import from `src/` only |
| `tests/` | Real file paths; skip with `pytest.mark.skipif` when files absent |
| `manuscript/` | Self-contained prose sections referencing the integration |

---

## Key Source Modules

| Module | Role |
|---|---|
| `src/fonds_reader.py` | Reads `fonds/templates/template_bibliography`, `template_contacts`, `template_datasets` |
| `src/rules_applier.py` | Loads `rules/templates/template_project_rules` and `template_manuscript_rules` |
| `src/strong_rule_evaluator.py` | Semantic evaluation of strong rule YAML against a runtime context dict |
| `src/tools_invoker.py` | Discovers `tools/templates/template_code_executor` and other tool manifests |
| `src/integration.py` | Orchestrates all three into a combined demo result dict |

---

## Commands

Run from the repository root:

```bash
# Tests
uv run pytest projects/templates/template_pools_rules_tools/tests/ -v \
    --cov=projects/templates/template_pools_rules_tools/src \
    --cov-fail-under=90

# Scripts
uv run python projects/templates/template_pools_rules_tools/scripts/01_validate_sources.py
uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
uv run python projects/templates/template_pools_rules_tools/scripts/03_generate_manuscript.py
uv run python projects/templates/template_pools_rules_tools/scripts/04_validate_strong_rules.py
```

---

## Resilience Policy

Resource directories may not all exist (other subagents may still be populating
them). All `src/` functions use graceful fallbacks:

- Return `None` or empty collections when paths are absent
- Log a warning but do not raise
- Tests skip via `pytest.mark.skipif` when required files are missing

---

## Parent Docs

- `fonds/AGENTS.md` — fond conventions
- `rules/AGENTS.md` — rule conventions
- `tools/AGENTS.md` — tool conventions
- `projects/AGENTS.md` — project lifecycle rules

## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-pools-rules-tools/SKILL.md`](.agents/skills/template-pools-rules-tools/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.
