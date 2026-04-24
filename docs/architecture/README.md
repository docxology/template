# architecture/ - Architecture Documentation

> **System design and implementation** details

**Quick Reference:** [Two-Layer Architecture](two-layer-architecture.md) | [Thin Orchestrator](thin-orchestrator-summary.md) | [Decision Tree](decision-tree.md)

## Purpose

The `architecture/` directory contains detailed documentation about the system architecture, design patterns, and implementation decisions. Examples that need a concrete `projects/{name}/` path should use **`projects/code_project/`** only; [`projects/`](../../projects/README.md) is otherwise a rotating set (see [`../_generated/active_projects.md`](../_generated/active_projects.md)).

## Contents

| File | Purpose | Audience |
|------|---------|----------|
| [`AGENTS.md`](AGENTS.md) | Technical guide for this directory | Maintainers, agents |
| [`two-layer-architecture.md`](two-layer-architecture.md) | two-layer architecture guide | Developers, architects |
| [`thin-orchestrator-summary.md`](thin-orchestrator-summary.md) | Thin orchestrator pattern implementation | Developers |
| [`decision-tree.md`](decision-tree.md) | Decision tree for code placement | Developers |
| [`migration-from-flat.md`](migration-from-flat.md) | Migration from a flat repo layout | Maintainers |
| [`testing-strategy.md`](testing-strategy.md) | Testing strategy and coverage | Developers |

## Quick Navigation

### Understanding the Architecture
1. Read [`../core/architecture.md`](../core/architecture.md) - System overview
2. Study [`two-layer-architecture.md`](two-layer-architecture.md) - architecture guide
3. Learn [`thin-orchestrator-summary.md`](thin-orchestrator-summary.md) - Pattern details

### Making Design Decisions
→ Use [`decision-tree.md`](decision-tree.md) - Code placement guide

## Related Documentation

- **[`../core/architecture.md`](../core/architecture.md)** - System architecture overview
- **[`../core/workflow.md`](../core/workflow.md)** - Development workflow
- **[`../development/`](../development/)** - Development and contribution guides

## See Also

- [`../documentation-index.md`](../documentation-index.md) - documentation index
- [`../README.md`](../README.md) - Documentation hub overview





