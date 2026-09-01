# manuscript/figures - AGENTS.md

Generated artifacts — do not hand-edit. Every PNG here is produced by
`scripts/generate_figures.py` from `data/example_descriptor.json` and the fixture
bytes, with all computation in `src/data_descriptor/`. To change a figure, change
the descriptor, the fixture data, or the tested preparer, then regenerate:

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_figures.py
```

Keep the figure set and the embedding `![...](figures/<name>.png){#fig:<name>}`
blocks in the manuscript in sync: a figure with no prose embed does not render,
and an embed with no file breaks the cross-link and drift gates.
