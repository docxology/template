# template_active_inference docs

Documentation for the public Active Inference multi-track exemplar (analytical,
pymdp, sheaf manuscript, Lean/GNN/ontology, provenance, replay matrix,
counterexamples, toy sweeps, uncertainty, benchmark, model-checking, interop,
semantic gluing, dependency graph, evidence fields, release bundle, theorem
traceability, gate ergonomics, generated track-improvement scope, blocked-scope,
and adversarial audit) composed into a sheaf manuscript.

- `conceptual-foundations.md` — the intellectual grounding: Active Inference
  and EFE, cellular sheaves over the IMRAD poset, semantic gluing, the Lean 4
  boundary, GNN/AIO notation contracts, and further reading.
- `reference/method-inventory.md` — generated coverage for every Python `def`
  and `class` under `src/` and `scripts/`; refresh with
  `uv run python scripts/generate_method_inventory.py --check`.
- `reference/rendering-reproducibility.md` — authored contract for sheaf
  composition, hydration, figure rendering, artifact regeneration order, and
  root output parity.
- Visualization quality is validated through render metrics, source maps,
  hashes, section bindings, and per-figure claim lanes in
  `output/data/figure_source_map.json` and
  `output/reports/visualization_quality_audit.json`.
- `thermo-nuclear-code-quality-review.md` — completed maintainability backlog
  (shared JSON I/O helpers, test-speed ergonomics, mypy override correction).
- See the project root `README.md` for the overview and `AGENTS.md` for agent
  guidance; per-directory `README.md`/`AGENTS.md` pairs document each component.

Verify the documentation and output contracts from the project root:

```bash
uv run python scripts/check_documentation_contract.py --check
uv run python scripts/generate_method_inventory.py --check
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/validate_outputs.py
uv run pytest tests/ --cov=src --cov-fail-under=90
```

From the template repository root:

```bash
./run.sh --pipeline --project templates/template_active_inference --core-only --skip-infra
```
