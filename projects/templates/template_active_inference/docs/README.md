# template_active_inference docs

Documentation for the public Active Inference multi-track exemplar (analytical,
pymdp, sheaf manuscript, Lean/GNN/ontology, provenance, replay matrix,
counterexamples, toy sweeps, uncertainty, benchmark, model-checking, interop,
semantic gluing, dependency graph, evidence fields, release bundle, theorem
traceability, gate ergonomics, generated track-improvement scope, blocked-scope,
and adversarial audit) composed into a sheaf manuscript.

- `reference/method-inventory.md` — generated coverage for every Python `def`
  and `class` under `src/` and `scripts/`; refresh with
  `uv run python scripts/generate_method_inventory.py`.
- `reference/rendering-reproducibility.md` — authored contract for sheaf
  composition, hydration, figure rendering, artifact regeneration order, and
  root output parity.
- See the project root `README.md` for the overview and `AGENTS.md` for agent
  guidance; per-directory `README.md`/`AGENTS.md` pairs document each component.

Run the project:

```bash
uv run python -m pytest projects/templates/template_active_inference/tests -q
./run.sh --pipeline --project template_active_inference --core-only --skip-infra
```
