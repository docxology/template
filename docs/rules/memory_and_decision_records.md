# Memory and Decision Records

## Overview

Decision memory in this repository is intentionally tiered. The goal is to
leave enough rationale for future agents to avoid repeating mistakes without
creating stale ledgers that compete with generated facts.

## Where Rationale Belongs

| Need | Use | Rule |
| --- | --- | --- |
| Counterintuitive local choice | `WHY:` comment beside the artifact | Explain why this shape exists or what failed before; avoid comments that restate code. |
| Repository architecture or workflow rule | ADR under `docs/architecture/adrs/` | New constitutional rules need context, decision, consequences, alternatives, and references. |
| Project plan or invariant | Project `TODO.md`, `ISA.md`, or `docs/` note | Keep the scope local to the project unless it changes the template contract. |
| Real failure lesson | Failure-autopsy note in project docs or git history | Record what broke, why it hurt, and what to do differently. |
| Agent preference or local workspace fact | `.cursor/hooks/state/continual-learning-memory.json` | Gitignored and local only; do not treat it as public repository truth. |
| Low-stakes reversible choice | No durable record | If it can be undone quickly and affects no public contract, skip the archive. |

## Volatile Facts

Do not copy measured counts, coverage percentages, test totals, public project
rosters, or infrastructure file counts into local memory or durable prose unless
the text points to the generated source of truth.

- Public project names: [`docs/_generated/active_projects.md`](../_generated/active_projects.md)
- Measured counts and gate snapshots: [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md)

The helper `infrastructure.core.agent_memory.audit_memory_payload()` returns
advisories for local memory bullets that hard-code those volatile facts.

## Assumptions

Use inline assumption tags only where the assumption is load-bearing:

```text
ASSUMES: <condition that makes this decision valid>
REVIEW_BY: YYYY-MM-DD
```

Do not add a global assumption register unless it is generated or actively
validated. A stale central assumption register is worse than no register because
it looks authoritative while silently drifting.

## RedTeam and Verifiers

Any new verifier, schema, quality gate, or RedTeam-derived hardening rule must
have at least one negative-control test. The negative control should build or
describe a known-wrong artifact that the verifier rejects.

Good negative controls include:

- a tag-only JSON payload that lacks required fields;
- a tampered fixture whose recorded hash no longer matches;
- a manuscript token that looks valid but is not hydrated;
- a project path or roster claim that bypasses generated documentation.

Do not claim a verifier is strong just because it passes on the healthy fixture.
The test must prove that it fails on a plausible wrong input.

## Review Checklist

- Does the rationale live closest to where future confusion will happen?
- Is a structural rule captured in an ADR rather than scattered prose?
- Are volatile facts linked to generated docs instead of copied?
- Does every new verifier-like rule include a negative control?
- Is the decision low-stakes and reversible enough to leave undocumented?
