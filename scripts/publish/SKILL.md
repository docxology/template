---
name: template-publish
description: |
  Publishing scripts for PyPI release validation and post-publish verification.
  Includes TestPyPI upload, fresh-venv install verification, and production
  artifact publishing. Designed for non-interactive CI/CD and agent workflows.
---
# SKILL: template-publish

Publishing automation scripts.

## Invocation

```bash
uv run python scripts/publish/test_pypi.py
uv run python scripts/publish/verify_install.py
uv run python scripts/publish/publish_project_release.py --project <name>
```

## Related

- `scripts/publish/AGENTS.md` — detailed publishing documentation
- `infrastructure/publishing/` — publishing modules