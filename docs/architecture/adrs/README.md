# Architecture Decision Records (ADRs)

This directory captures significant architectural decisions made during the development of the Research Project Template.

## What is an ADR?

An Architecture Decision Record is a lightweight document that captures an important architectural choice along with its context and consequences. Once accepted, ADRs are immutable — superseded decisions get a new record.

## Format

Each ADR follows this structure:

- **Title** — Short descriptive name
- **Status** — Proposed / Accepted / Superseded / Deprecated
- **Context** — What forces are at play? What problem are we solving?
- **Decision** — What was decided?
- **Consequences** — Positive and negative outcomes
- **Alternatives Considered** — What else was evaluated?
- **References** — Links to related docs, code, or ADRs

## ADR Index

| # | Title | Status |
|---|-------|--------|
| [000](000-two-layer-architecture.md) | Two-Layer Architecture | Accepted |
| [001](001-thin-orchestrator-pattern.md) | Thin Orchestrator Pattern | Accepted |
| [002](002-declarative-dag-pipeline.md) | Declarative DAG Pipeline | Accepted |
| [003] — | *Withdrawn; covered by ADR 002* | — |
| [004](004-zero-mock-testing-policy.md) | Zero-Mock Testing Policy | Accepted |

> **Note:** ADR 003 was withdrawn — its scope (declarative pipeline definition) was absorbed into ADR 002.

## Reading Order

Start with **ADR 000** (Two-Layer Architecture) for foundational context, then proceed sequentially. ADR 001–004 build on each other.

## See Also

- [`docs/architecture/two-layer-architecture.md`](../two-layer-architecture.md) — Detailed architecture guide
- [`docs/architecture/decision-tree.md`](../decision-tree.md) — Code placement decision tree
- [`docs/architecture/thin-orchestrator-summary.md`](../thin-orchestrator-summary.md) — Pattern implementation