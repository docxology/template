# Sheaf composition package

Implementation of the sheaf manuscript composition: registry tracks plus manifest rows resolve through generated and markdown renderers into flat manuscript sections, coverage JSON, heatmap/page artifacts, and hydrated publication text.

- `models.py` — data models for tracks, sections, and the sheaf manifest.
- `manifest.py` — load/validate the `manuscript/sheaf/` manifest and tracks.
- `registry.py` — track/fragment registry.
- `renderers.py` — per-track fragment renderers.
- `compose.py` — glue fragments into composed manuscript sections.
- `coverage.py` — verify every declared track/section fragment is present.
- `laws.py` — verify the sheaf axioms over the IMRAD base poset (poset, presheaf,
  separation, gluing, typing, compositionality).

## Verify the sheaf laws

```bash
# Oracle (all-pass on a well-formed manifest):
uv run python -c "from pathlib import Path; from manuscript.sheaf import verify_sheaf_laws; print(verify_sheaf_laws(Path('.')).summary())"

# Enforced as part of the strict compose gate:
uv run python scripts/compose_manuscript.py --validate-only --strict

# Negative controls (each law is proven to be falsifiable):
uv run pytest tests/test_sheaf_laws.py -q
```

The laws turn "sheaf" from notation into a machine-checked claim; they verify the
sheaf *axioms* on a finite base poset, not sheaf *cohomology*. See
[`AGENTS.md`](AGENTS.md) for the per-law table.
