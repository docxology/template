# scripts - template_data_descriptor

Use the monorepo pipeline scripts from the repository root for normal test/render stages.

`generate_release_artifacts.py` creates deterministic descriptor-review artifacts from `data/example_descriptor.json`: descriptor readiness report, metadata-only release bundle manifest, and field-constraint summary.

```bash
uv run python projects/templates/template_data_descriptor/scripts/generate_release_artifacts.py
```
