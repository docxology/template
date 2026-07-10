# scripts - template_data_descriptor

Thin orchestrators. All computation is delegated to `src/data_descriptor/`; these
scripts only load the descriptor, plot or serialize, and print output paths.

Use the monorepo pipeline scripts from the repository root for normal
test/render stages. Two project-local scripts are provided:

`generate_figures.py` renders the five manuscript figures into
`manuscript/figures/` from `data/example_descriptor.json` and the fixture bytes
(schema overview, file inventory, provenance flow, quality gate, checksum
verification):

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_figures.py
```

`generate_release_artifacts.py` creates deterministic descriptor-review artifacts
under `output/reports/`: descriptor readiness report, metadata-only release
bundle manifest, and field-constraint summary:

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_release_artifacts.py
```
