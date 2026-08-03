# tests - template_data_descriptor

Zero-mock tests over real fixture dictionaries, real temporary files, and real
generated PNGs. See [`AGENTS.md`](AGENTS.md) for the full contract and
per-file coverage map.

Run from the monorepo root:

```bash
uv run pytest projects/templates/template_data_descriptor/tests --cov=projects/templates/template_data_descriptor/src --cov-fail-under=90
```
