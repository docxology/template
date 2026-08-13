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
| Injected manuscript values | `projects/<name>/output/data/manuscript_variables.json` plus the project producer/test |
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

Audit all public exemplars in the generated roster
([`active_projects.md`](../_generated/active_projects.md)) at the source or
rendered boundary:

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
that no figures exist. The flag verifies non-empty accessibility metadata, not
its descriptive quality; inspect the rendered HTML and PDF with human and
assistive-technology review.

## Authoring Rules

- Put project methods logic in `projects/<name>/src/`.
- Keep `projects/<name>/scripts/` as thin orchestrators.
- Declare stage inputs, outputs, gates, and `definition_of_done` in
  `pipeline.yaml`.
- Assign every stage a stable `key`, executable `script` or executor `method`,
  failure code, and at least one output artifact.
- Keep artifact paths repository-relative and free of parent traversal.
- Explain the method in manuscript source files, not generated `output/`.
- Generate every result-bearing manuscript value and caption fragment from
  typed analysis outputs; test token completeness before hydration.
- Produce in dependency order: source inputs/configuration → analysis tables and
  figures → manuscript variables/figure registry → hydrated manuscript →
  rendered artifacts → validation/evidence/artifact receipts.
- Refresh pipeline outputs before treating artifact manifests or evidence
  registries as current; never hand-edit a downstream registry or receipt to
  clear a gate.
- Treat the methods plan as a traceability map: method prose → declared stages
  → generated figures/claims → evidence and artifact reports → rendered output.

## Publication Gate

A project is not methods-ready when any of these conditions holds:

- the manuscript methods/methodology section is missing;
- the artifact manifest is absent, invalid, stale, or does not match the current
  output tree;
- the evidence registry is missing or not source-current;
- a stage lacks `definition_of_done` or declared output artifacts;
- an executable stage script or verification command is missing/invalid;
- dependency edges are orphaned;
- result-bearing tokens are unresolved or not backed by the current analysis;
- a referenced figure is absent, unregistered, or lacks reviewed accessibility
  description; or
- statistical procedures, exclusions, deviations, and limitations are not
  sufficiently specified to reproduce and interpret the result.

Use this gate alongside claim-support/citation review, reproducibility audit,
rendered accessibility inspection, PDF validation, owner approval, and explicit
release authority. These are separate outcomes.
