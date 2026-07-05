# template_pools_rules_tools

**Pools, Rules, and Tools: A Template-Integrated Resource Architecture**

A meta-project exemplar demonstrating the integration of three top-level resource directories:

| Directory | Role |
|---|---|
| `fonds/` | Stable data resource pools (bibliographies, contacts, datasets) |
| `tools/` | Executable tool entry points (code executors, validators, skills) |
| `rules/` | Soft (prompt-like) and strong (formal) rule specifications |

## Purpose

This project shows agents and developers how to:

1. **Read fonds** — load bibliographic references, contacts, and dataset metadata from `fonds/templates/`
2. **Apply rules** — discover and parse soft guidelines and strong constraint schemas from `rules/templates/`
3. **Invoke tools** — enumerate tool manifests and validate entrypoint scripts from `tools/templates/`
4. **Integrate all three** — orchestrate a combined validation and reporting pipeline

## Structure

```
template_pools_rules_tools/
├── src/
│   ├── fonds_reader.py       # Read fonds from fonds/templates/
│   ├── rules_applier.py      # Load and apply rules from rules/templates/
│   ├── tools_invoker.py      # Discover tools from tools/templates/
│   └── integration.py        # Integration orchestrator
├── scripts/
│   ├── 01_validate_sources.py    # Validate all sources exist and are well-formed
│   ├── 02_run_integration.py     # Run the full integration demo
│   └── 03_generate_manuscript.py # Generate manuscript variables
├── tests/
│   ├── test_fonds_reader.py
│   ├── test_rules_applier.py
│   ├── test_tools_invoker.py
│   └── test_integration.py
└── manuscript/
    ├── config.yaml
    ├── 01_abstract.md … 07_conclusion.md
    └── references.bib
```

## Quick Start

From the repository root:

```bash
# Run tests
uv run pytest projects/templates/template_pools_rules_tools/tests/ -v

# Validate sources
uv run python projects/templates/template_pools_rules_tools/scripts/01_validate_sources.py

# Run integration demo
uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
```

## When to use this template

Use this project when you need to:

- **Demonstrate** how a research project integrates multiple resource directories (fonds, tools, rules) in a single pipeline
- **Validate** that your fonds, tools, and rule infrastructure modules are correctly wired and discoverable
- **Onboard** new teams to the three-resource architecture with a concrete, runnable example
- **Test** cross-cutting concern integration where fonds supply data, rules govern validation, and tools execute transforms
- **Extend** the architecture by adding new resource types; copy this project as a starting point for integration testing

This template is ideal for platform teams, CI engineers, and infrastructure maintainers who need a self-validating meta-project that exercises all three resource layers without coupling to a specific domain science.

## Publication and rendering

This project is designed to run **inside** the [docxology/template](https://github.com/docxology/template) monorepo. All paths resolve relative to the repository root. The project reads public tracked exemplars from `fonds/templates/`, `tools/templates/`, and `rules/templates/` — these must be present.

```bash
# From the template repository root
uv sync
uv run pytest projects/templates/template_pools_rules_tools/tests/ -v
uv run python projects/templates/template_pools_rules_tools/scripts/02_run_integration.py
```

## Dependencies

- `pyyaml` — YAML manifest loading (always available in the template environment)

## See Also

- `fonds/AGENTS.md` — fond discovery and validation conventions
- `rules/AGENTS.md` — rule loading and enforcement conventions
- `tools/AGENTS.md` — tool discovery and invocation conventions
