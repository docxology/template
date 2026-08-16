# scripts - template_data_descriptor

Thin orchestrators. All computation is delegated to `src/data_descriptor/`;
these scripts only select the project root, call typed producer APIs, serialize
already-tested objects where applicable, and print output paths.

Use the monorepo pipeline scripts from the repository root for normal
test/render stages. Two project-local scripts are provided:

`generate_figures.py` delegates to `generate_descriptor_figure_assets()`, which
renders the five manuscript figures into `manuscript/figures/` from
`data/example_descriptor.json` and the fixture bytes, then mirrors and registers
the exact run under `output/figures/` (schema overview, file inventory,
provenance flow, quality gate, checksum verification):

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_figures.py
```

`generate_release_artifacts.py` creates deterministic descriptor-review artifacts
under `output/reports/`: descriptor readiness report, metadata-only release
bundle manifest, and field-constraint summary:

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_release_artifacts.py
```
