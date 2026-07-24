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
| Figure provenance | `projects/<name>/output/figures/figure_registry.json` when present |
| Source-backed claims | `projects/<name>/data/claim_ledger.yaml` when present |
| Experiment/review design | `projects/<name>/experiment_plan.yaml` when present |
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
name. The validator also checks DAG orphan edges, executable script paths,
built-in executor method names, failure codes, artifact-path containment,
verification-command script resolution, and current artifact-manifest hashes.
Project-local stage commands receive explicit `--project` context. A rendered
artifact manifest produced by `refresh_artifact_manifests.py` is an integrity
snapshot, not stage provenance; the audit reports that distinction as a warning
until per-stage manifests are produced by `PipelineExecutor`. Exit codes are
`0` clean/warnings, `1` validation errors, and `2` invalid
invocation/configuration.

Run the focused tests:

```bash
uv run pytest tests/infra_tests/methods -q
```

For a migration-safe visual accessibility check, require explicit alt text for
every manuscript-referenced figure during the publication audit:

```bash
uv run python -m infrastructure.validation.cli publication-audit \
  --project templates/template_code_project --rendered \
  --require-figure-accessibility --format markdown
```

This flag is intentionally opt-in while existing exemplars are migrated. The
ordinary publication audit still blocks missing registries and unregistered
references, and it never treats a missing optional figure registry as proof
that no figures exist.

## Authoring Rules

- Put project methods logic in `projects/<name>/src/`.
- Keep `projects/<name>/scripts/` as thin orchestrators.
- Declare stage inputs, outputs, gates, and `definition_of_done` in
  `pipeline.yaml`.
- Assign every stage a stable `key`, executable `script` or executor `method`,
  failure code, and at least one output artifact.
- Keep artifact paths repository-relative and free of parent traversal.
- Explain the method in manuscript source files, not generated `output/`.
- Refresh pipeline outputs before treating artifact manifests or evidence
  registries as current.
- Treat the methods plan as a traceability map: method prose → declared stages
  → generated figures/claims → evidence and artifact reports → rendered output.

## Publication Gate

A project is not methods-ready when any of these are missing:

- manuscript methods/methodology section
- artifact manifest
- artifact manifest hashes match the current output tree
- evidence registry
- stage `definition_of_done`
- declared stage output artifacts
- executable stage script and verification command
- no orphaned dependency edges

Use this gate alongside claim verification, reproducibility audit, and PDF
validation.
