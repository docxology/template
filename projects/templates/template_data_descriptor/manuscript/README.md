# manuscript - template_data_descriptor

Full manuscript for the data descriptor exemplar, rendered by the monorepo
pipeline (Pandoc). Sections, in render order:

- `00_abstract.md` — abstract
- `01_introduction.md` — background and what the template provides
- `02_data_description.md` — the demonstration dataset and file inventory
- `03_schema.md` — schema / data dictionary and schema fingerprint
- `04_provenance.md` — provenance chain
- `05_quality_validation.md` — validation gate and descriptor↔file verification
- `06_usage_notes.md` — regenerating artifacts and forking guidance
- `99_references.md` — references

Figures live under [`figures/`](figures/README.md) and are embedded in prose with
`![...](figures/<name>.png){#fig:<name>}` blocks. Configuration lives in
`config.yaml` (forkable defaults in `config.yaml.example`). Every quantitative
claim is derived from `data/example_descriptor.json` and the tested
`src/data_descriptor/` package — the prose transcribes no volatile numbers.
