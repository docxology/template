# template_active_inference docs

Documentation for the public Active Inference multi-track exemplar (analytical,
pymdp, sheaf manuscript, Lean/GNN/ontology) composed into a sheaf manuscript.

- `reference/` — reference and generated material.
- See the project root `README.md` for the overview and `AGENTS.md` for agent
  guidance; per-directory `README.md`/`AGENTS.md` pairs document each component.

Run the project:

```bash
uv run python -m pytest projects/template_active_inference/tests -q
./run.sh --pipeline --project template_active_inference --core-only --skip-infra
```
