# docs/ — template_autopoiesis

## What this repo is

A combinatoric **grammar** that deterministically generates whole runnable
child projects — `src/`, `tests/`, `scripts/`, and `manuscript/` — selected by
a seed from a grammar, with recompute-based provenance verification and
sealing. Public canonical exemplar of the Research Project Template
([`projects/templates/AGENTS.md`](../AGENTS.md)); see the repo
[`README.md`](../README.md) for scope and DOI.

## Directory map

| Path | Role |
| --- | --- |
| `src/` | Grammar, expansion, materialization, sealing, integrity, honesty, figure, and manuscript-contract modules (see `src/README.md`, `src/AGENTS.md`) |
| `src/primitives/` | Primitive dynamics/graph/optimization/signal/statistics registries |
| `scripts/` | Thin orchestrators: archetype/child realization, sealing, cover art, manuscript-asset and variable generation |
| `tests/` | Zero-mock test suite incl. property-invariant, stress, and meta-teeth tests |
| `manuscript/` | Section sources, config, references for the rendered PDF |
| `data/` | Authored source-data overlays (e.g. `claim_ledger.yaml` mapping manuscript claims to evidence identifiers) |
| `output/` | Generated evidence (never hand-edited) |

## How to run / test

From the template monorepo root (`projects/templates/template_autopoiesis/`
is the project):

```bash
uv run pytest projects/templates/template_autopoiesis/tests \
    --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90
uv run python scripts/runner/execute_pipeline.py --project templates/template_autopoiesis --core-only
```

Project-local scripts (see `scripts/README.md`):

```bash
uv run python projects/templates/template_autopoiesis/scripts/realize_archetypes.py
uv run python projects/templates/template_autopoiesis/scripts/realize_child_full.py
uv run python projects/templates/template_autopoiesis/scripts/seal_child.py
uv run python projects/templates/template_autopoiesis/scripts/04_seal.py
```

## Documentation in this tree

- [`AGENTS.md`](AGENTS.md) — agent-facing layout, conventions, and maintenance notes.
- Sibling guides live in the repo root (`README.md`, `SPEC.md`, `ISA.md`,
  `STANDALONE.md`, `TODO.md`); this `docs/` tree is the human entry point.

## Status

Publication-track exemplar: `manuscript/` is complete and gate-guarded; this
docs/ tree was added by the docs-audit pass of 2026-08-29.
