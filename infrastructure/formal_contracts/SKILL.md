---
name: infrastructure-formal-contracts
description: Skill for the typed formal-contracts package — composing and machine-checking well-typed manuscripts (typed claims, evidence tiers, resolvable formal statements, acyclic dependency DAGs).
---

# Formal Contracts

## Commands

```bash
uv run pytest tests/infra_tests/formal_contracts -q
uv run python -c "from infrastructure.formal_contracts import read_blocks, compose, check_manuscript; ms = compose(list(read_blocks(open('manuscript.md').read()))); print(check_manuscript(ms).diagnostics)"
```

## When to use

- Checking that manuscript claims carry evidence of a declared tier.
- Verifying formal statements resolve to registered definitions/theorems.
- Validating a manuscript block DAG: unique ids, acyclicity, no orphans.

## API

`compose`, `check_manuscript`, `compose_manuscripts`, `read_blocks`,
`Manuscript`, `Report`, `Diagnostic`, `FormalCode`, block types
(`Claim`, `Evidence`, `FormalStatement`, `Derivation`, `Figure`, `Table`,
`Dataset`, `Section`).

## Honesty

Preorder-enriched graph + monoidal composition; NOT a topos. See module
docstrings.
