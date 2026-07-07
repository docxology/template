---
name: template-autopoiesis
description: Combinatoric grammar that deterministically generates whole runnable child projects (src/, tests/, scripts/, manuscript/) from a seed — recompute-based provenance verification and a falsifiable honesty manifest against green-by-construction test theater.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, autopoiesis, grammar, provenance, generative]
---

# template-autopoiesis

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_autopoiesis/`. Load this when working inside the
project.

## When to Use

- Working inside the `template_autopoiesis` exemplar — running the grammar,
  materializing child projects, or editing source.
- Forking this exemplar to build a different combinatoric project-generator.
- Validating that a materialized child project's tests, coverage, and
  recompute-verified provenance still hold after a grammar change.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_autopoiesis/tests --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90

# Materialize a child project from the grammar (writes a full runnable tree)
uv run python projects/templates/template_autopoiesis/scripts/autopoiesis.py materialize --out-root /tmp/children

# Realize a full archetype end-to-end (spec → child → seal)
uv run python projects/templates/template_autopoiesis/scripts/realize_child_full.py

# Seal a materialized child with QR provenance
uv run python projects/templates/template_autopoiesis/scripts/seal_child.py
```

## Pitfalls

- **Keep scripts thin.** Business logic belongs in `src/` (`grammar.py`,
  `expand.py`, `materialize.py`, `realize.py`, `sealing.py`, `verify.py`), not
  in `scripts/`.
- **Recompute, never trust recorded hashes.** The whole point of this
  exemplar is that a child's provenance is re-derived from disk at verify
  time, not read from a cached manifest.
- **No mocks.** All tests must use real generated files and real computation.
- **Outputs are disposable.** Never hand-edit `output/`; regenerate from the
  grammar in `manuscript/config.yaml`.
- **Run from the repo root.** Commands assume the template monorepo root as
  working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- Grammar syntax: [`SYNTAX.md`](../../../SYNTAX.md)
- Standalone usage: [`STANDALONE.md`](../../../STANDALONE.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../AGENTS.md)
