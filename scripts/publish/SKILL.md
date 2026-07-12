---
name: template-publish
description: |
  Publishing scripts for DOI-bearing project releases, optional mirror uploads,
  PyPI release validation, post-publish verification, and publication export.
  Use with docs/guides/publication-runbook.md for standalone GitHub + Zenodo
  release workflows.
---
# SKILL: template-publish

Publishing automation scripts.

Start with [`docs/guides/publication-runbook.md`](../../docs/guides/publication-runbook.md)
for the modular path from rendered project to standalone public GitHub mirror,
real Zenodo DOI, optional mirrors, and archival handoff.

## Invocation

```bash
uv run python scripts/publish/test_pypi.py
uv run python scripts/publish/verify_install.py
uv run python scripts/publish/publish_project_release.py \
  --project templates/<name> --tag v1.0.0 --repo owner/repo
uv run python scripts/publish/upload_template_project.py --project <name>
```

## Related

- `scripts/publish/AGENTS.md` — detailed publishing documentation
- `infrastructure/publishing/` — publishing modules
