# Methods Orchestration Package

## Purpose

`infrastructure.methods` turns existing repo contracts into an explicit methods
orchestration plan:

- pipeline stages and `contract:` metadata from `pipeline.yaml`
- manuscript method sections — a file qualifies when its **name** carries a
  method token (`method`/`methodology`/`experimental_setup`/`protocol`) **or**
  its body contains a top-level Methods/Methodology/Protocol heading. The
  heading fallback covers exemplars whose Methods content lives in a
  differently-named section file (e.g. `template_template`'s `03a_architecture.md`).
- `artifact_manifest.json`
- `evidence_registry.json`
- validation commands that prove the methods surface is current

It is a Layer-1 read-only orchestration contract. Do not put scientific
algorithms or project analysis logic here.

## Files

| File | Role |
| --- | --- |
| `models.py` | Dataclasses for keyed stages, versioned plans, per-project audits, aggregate reports, and issues. |
| `orchestration.py` | Single/batch plan builders, validator, and Markdown renderer using the canonical pipeline-source resolver. |
| `cli.py` | `python -m infrastructure.methods plan` command. |
| `__main__.py` | Module entry point. |

## Contracts

- Preserve the thin-orchestrator pattern: scripts run stages; this package maps
  contracts and validation surfaces.
- Keep paths repo-relative in public payloads so generated reports are stable.
- Methods source precedence is explicit path, project `methods_pipeline.yaml`,
  project `pipeline.yaml`, repository definition, then installed package data.
- Rendered mode treats missing artifact manifests and evidence registries as
  publication-blocking errors. Source mode validates authoring contracts only.
- Stage `key` is execution identity; human-readable names and name-based
  dependency declarations remain display/telemetry values.
- CLI exits `0` for clean/warnings, `1` for validation errors, and `2` for
  invalid invocation/configuration.
- Stage `script` values must already be repo-relative paths (`scripts/...` or
  `projects/...`); verification commands expand `{project}` only.

## Tests

```bash
uv run pytest tests/infra_tests/methods -q
```
