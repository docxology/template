# Methods Orchestration

Methods orchestration is the repo-level contract that keeps the written methods
section, pipeline DAG, artifacts, evidence registry, and validation commands in
sync. It does not run analysis itself; it makes the existing method surfaces
inspectable before publication.

## What It Connects

| Surface | Source |
| --- | --- |
| Pipeline stages | canonical resolver: explicit path → project methods/pipeline → repository/package definition |
| Stage inputs and outputs | each stage `contract:` block |
| Manuscript methods prose | `projects/<name>/manuscript/*method*.md` |
| Evidence links | `projects/<name>/output/reports/evidence_registry.json` |
| Artifact hashes and stage outputs | `projects/<name>/output/reports/artifact_manifest.json` |
| Validation commands | `infrastructure.methods` generated plan |

## Commands

Render a Markdown plan:

```bash
uv run python -m infrastructure.methods plan --project templates/template_code_project --format markdown
```

Render a machine-readable plan and fail on missing publication-critical
surfaces:

```bash
uv run python -m infrastructure.methods plan --project templates/template_code_project --format json --check
```

Audit all 24 public exemplars at the source or rendered boundary:

```bash
uv run python -m infrastructure.methods plan --all-public --artifact-mode source --format json
uv run python -m infrastructure.methods plan --all-public --artifact-mode rendered --format json
```

`--project` and `--all-public` are mutually exclusive. Rendered mode is the
default. Every plan carries `schema_version` and `artifact_mode`; every stage
carries its stable execution `key` while retaining its historical display
name. Exit codes are `0` clean/warnings, `1` validation errors, and `2` invalid
invocation/configuration.

Run the focused tests:

```bash
uv run pytest tests/infra_tests/methods -q
```

## Authoring Rules

- Put project methods logic in `projects/<name>/src/`.
- Keep `projects/<name>/scripts/` as thin orchestrators.
- Declare stage inputs, outputs, gates, and `definition_of_done` in
  `pipeline.yaml`.
- Explain the method in manuscript source files, not generated `output/`.
- Refresh pipeline outputs before treating artifact manifests or evidence
  registries as current.

## Publication Gate

A project is not methods-ready when any of these are missing:

- manuscript methods/methodology section
- artifact manifest
- evidence registry
- stage `definition_of_done`
- declared stage output artifacts

Use this gate alongside claim verification, reproducibility audit, and PDF
validation.
