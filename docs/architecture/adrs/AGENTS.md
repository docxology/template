# Architecture Decision Records (ADRs)

## Overview

Technical guide for `docs/architecture/adrs/` — lightweight, numbered decision records capturing key architectural choices in the template repository.

## Files

| File | Purpose |
|------|---------|
| `000-two-layer-architecture.md` | Two-layer architecture (Infrastructure vs Project) |
| `001-thin-orchestrator-pattern.md` | Thin orchestrator pattern for pipeline scripts |
| `002-declarative-dag-pipeline.md` | Declarative DAG-based pipeline execution |
| `003-multi-format-rendering-and-toggles.md` | Multi-format rendering and per-format toggles |
| `004-zero-mock-testing-policy.md` | Zero-mock testing policy |

## Key Conventions

- ADRs are numbered sequentially (`NNN-short-title.md`).
- Each ADR follows the standard structure: Context, Decision, Consequences (positive/negative), Alternatives Considered.
- ADRs are immutable once accepted — superseded decisions get a new ADR that references the old one.
- Gaps in numbering *may* indicate withdrawn drafts; check the index. (A withdrawn slot may also be reused for a new decision — e.g., ADR 003 was reused on 2026-05-20 for multi-format rendering.)

## See Also

- [README.md](README.md) — Quick navigation
- [../two-layer-architecture.md](../two-layer-architecture.md) — Full two-layer architecture guide
- [../decision-tree.md](../decision-tree.md) — Code placement decision tree
