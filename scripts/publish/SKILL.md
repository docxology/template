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

## PyPI package checks

Use the credential-free adapter for a local package preview. The TestPyPI CLI
makes an actual sandbox transfer and requires explicit approval. The offline
verifier takes the original wheel path and SHA-256.
[Commands and locked tools](README.md#pypi-package-checks)

## Related

- [Publishing agent guide](AGENTS.md)
- [Publishing infrastructure](../../infrastructure/publishing/README.md)
