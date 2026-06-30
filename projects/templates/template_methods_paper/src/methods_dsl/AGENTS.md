# `template_methods_paper/src/methods_dsl/` - agent guide

## Purpose

A small, tested controlled-method specification language: the model
(`model.py`, `units.py`, `vocabulary.py`), four staged validation gates
(`validation.py`), a deterministic compiler (`compiler.py`), exporters
(`export.py`), and a provenance hash-chain (`trust.py`). Generalizes the
domain language of BPL (Biology Programming Language,
https://gitlab.com/bota-biosciences-public/bpl-code) from wet-lab protocols
to any controlled procedure. The manuscript describes this package itself as
its central subject.

## Rules

- Keep this subpackage standalone: import only stdlib, except
  `_logging.py`'s single sanctioned `infrastructure.core.logging.utils`
  import (declared in `manuscript/layer_contract.yaml`). No other module here
  imports `infrastructure.*` or a sibling project.
- Never render plots or write files here. Exporters return text
  (`to_worklist_markdown`, `to_csv_rows`, `to_mermaid`, `to_json`) or take an
  explicit `path: Path` (`write_csv`, `write_json`); matplotlib and the
  output-directory layout stay in `scripts/` (thin-orchestrator contract).
- Run validation gates in the fixed order `run_all_gates` defines
  (structural → semantic → plan → target); never reorder or skip a gate
  inside `compile_method`.
- Keep `compile_method` deterministic: the same `Method` must always produce
  the same `Plan.plan_hash` — sort before hashing, never rely on dict/set
  iteration order for anything that reaches the hash.
- Re-export the public surface from `src/__init__.py` so callers write
  `from src import compile_method` regardless of internal layout.

## See Also

- [`README.md`](README.md) - module-by-module file listing
- [`../AGENTS.md`](../AGENTS.md) - source-layer contract
- [`../../docs/architecture.md`](../../docs/architecture.md) - correspondence with BPL's compiler pipeline
