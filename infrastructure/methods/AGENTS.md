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
- `figure_registry.json` when the project publishes generated figures
- `data/claim_ledger.yaml` when the project declares source-backed claims
- `experiment_plan.yaml` when the project declares an experiment/review design
- validation commands that prove the methods surface is current

It is a Layer-1 read-only orchestration contract. Do not put scientific
algorithms or project analysis logic here.

## Files

| File | Role |
| --- | --- |
| `models.py` | Dataclasses for keyed stages, versioned plans, per-project audits, aggregate reports, and issues. |
| `orchestration.py` | Public plan builders, validator entry point, audits, and Markdown renderer. |
| `_plan_builder.py` | Private stage/section discovery and `{project}` expansion helpers. |
| `_plan_validation.py` | Private artifact/script/command validation helpers. |
| `_command_validation.py` | Canonical project, manuscript, runner, and stage command bindings. |
| `_evidence_validation.py` | Shared evidence registry freshness and experiment-plan validation. |
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
- Every stage declares exactly one executable `script` or executor `method`.
  Prose descriptions belong in the contract's `definition_of_done`.
- Stage keys are unique lowercase identifiers. Sequence fields are lists;
  flags are booleans, retries are non-negative integers, and hook deadlines
  are positive integers. Unknown fields and unknown original dependencies fail.
- CLI exits `0` for clean/warnings, `1` for validation errors, and `2` for
  invalid invocation/configuration.
- Expose optional figure, claim-ledger, and experiment-plan paths only when the
  source file exists; never imply that a missing surface was generated.
- When a project ships `methods_pipeline.yaml`, that file overrides
  `pipeline.yaml` and the repository default pipeline for plan discovery.
- `validate_methods_orchestration_plan(..., require_generated_artifacts=True)`
  (default) treats missing artifact manifests and evidence registries as
  publication-blocking errors. Source-only publication audits pass
  `require_generated_artifacts=False`.
- Stage `script` values must already be repo-relative paths (`scripts/...` or
  `projects/...`); verification commands expand `{project}` only.
- Commands use the canonical lexical project root and populated manuscript
  resolver, including `docs/manuscript/` when it supplies the source.
- Rendered evidence requires the supported compact registry schema, consistent
  counts, sampled facts supported by current sources, and resolvable evidence
  source paths. A compact sample is a summary rather than a proof of every claim.
- Optional experiment plans are checked with the shared project validator.

## Tests

```bash
uv run pytest tests/infra_tests/methods -q
```

Emitted runtime commands bind the exact declared YAML with `--pipeline-yaml`,
use canonical qualified project paths, and select `--mode live` for live/LLM
stages. The source catalog includes every declaration; execution delegates
selection, prerequisites, locking, source custody, and completion to the shared
immutable execution plan. Nested manuscript chapters are discovered recursively
while auxiliary agent/documentation Markdown is excluded.
