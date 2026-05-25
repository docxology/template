# Methods Orchestration Package

## Purpose

`infrastructure.methods` turns existing repo contracts into an explicit methods
orchestration plan:

- pipeline stages and `contract:` metadata from `pipeline.yaml`
- manuscript methods/methodology section files
- `artifact_manifest.json`
- `evidence_registry.json`
- validation commands that prove the methods surface is current

It is a Layer-1 read-only orchestration contract. Do not put scientific
algorithms or project analysis logic here.

## Files

| File | Role |
| --- | --- |
| `models.py` | Dataclasses for stages, plans, and validation issues. |
| `orchestration.py` | Plan builder, validator, and Markdown renderer. |
| `cli.py` | `python -m infrastructure.methods plan` command. |
| `__main__.py` | Module entry point. |

## Contracts

- Preserve the thin-orchestrator pattern: scripts run stages; this package maps
  contracts and validation surfaces.
- Keep paths repo-relative in public payloads so generated reports are stable.
- Treat missing method sections, artifact manifests, and evidence registries as
  publication-blocking errors.

## Tests

```bash
uv run pytest tests/infra_tests/methods -q
```
