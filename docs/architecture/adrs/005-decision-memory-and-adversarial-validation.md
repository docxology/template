# ADR 005: Decision Memory and Adversarial Validation Discipline

## Status

Accepted

## Context

The template repository already has strong generated truth surfaces:
[`docs/_generated/COUNTS.md`](../../_generated/COUNTS.md)
for measured counts and [`docs/_generated/active_projects.md`](../../_generated/active_projects.md)
for public project scope. It also has ADRs for constitutional architecture and
no-mock testing rules. What was missing was a clear decision about where
short-lived reasoning, durable rationale, assumptions, local agent memory,
failure lessons, and RedTeam-style verifier pressure should live.

Without a policy, agents can over-document every small choice, bury important
reasoning in gitignored memory, or copy volatile counts into prose. The opposite
failure is equally common: a counterintuitive local choice has no nearby "why,"
so the next agent simplifies it and breaks the system.

## Decision

Adopt a tiered decision-memory discipline:

- Use local `WHY:` comments only for counterintuitive choices whose rationale
  must appear beside the code, data, or prose that future readers will inspect.
- Use ADRs for repository architecture, workflow, validation, or documentation
  rules that should govern future work.
- Use project `TODO.md`, `ISA.md`, or project docs for active plans, invariants,
  scoped assumptions, and postmortems.
- Use `.cursor/hooks/state/continual-learning-memory.json` only for local
  agent preferences and workspace facts. Do not store public project rosters,
  test counts, coverage values, or infrastructure file counts there unless the
  entry points to generated documentation.
- Keep measured facts and public rosters in generated docs; human-authored docs
  must link to those sources rather than copying volatile literals.
- Any new verifier, schema, quality gate, or RedTeam-derived hardening rule must
  include at least one negative-control test proving a known-wrong artifact is
  rejected.
- Do not add a global assumption register unless it is generated or actively
  validated.

## Consequences

### Positive

- Future agents know where to put rationale without creating stale parallel
  ledgers.
- Generated docs remain the source of truth for volatile counts and rosters.
- Verifier claims become stronger because negative controls prove that a green
  gate can turn red on a known-wrong input.
- Project exemplars can propagate the same discipline through short links
  instead of duplicating policy prose.

### Negative

- Contributors must decide whether a decision deserves a nearby comment, an
  ADR, a project note, or no durable record.
- Some local memory entries become advisory rather than authoritative.
- Negative controls add small up-front test work whenever a verifier-like rule
  is added.

## Alternatives Considered

| Option | Reason for rejection |
| --- | --- |
| Global assumption register | High risk of becoming stale unless generated or checked. |
| Put all reasoning in comments | Clutters artifacts and hides cross-cutting architecture decisions. |
| Put all reasoning in ADRs | Too heavy for local implementation choices and short-lived project plans. |
| Trust local agent memory | Gitignored memory can drift and is not a public repository contract. |

## References

- [`docs/rules/memory_and_decision_records.md`](../../rules/memory_and_decision_records.md)
- [`docs/_generated/COUNTS.md`](../../_generated/COUNTS.md)
- [`docs/_generated/active_projects.md`](../../_generated/active_projects.md)
- [`infrastructure/core/agent_memory.py`](../../../infrastructure/core/agent_memory.py)
- [ADR 001: Thin Orchestrator Pattern](001-thin-orchestrator-pattern.md)
- [ADR 004: Zero-Mock Testing Policy](004-zero-mock-testing-policy.md)
