# Documentation Package

## Purpose

Documentation code generates and maintains live repo documentation surfaces:
figures, API references, architecture diagrams, active-project rosters,
publication matrices, and measured count facts. It should derive facts from the
tree instead of copying volatile literals into prose.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Figures and manuscript helpers | `figure_manager.py`, `generated_figure_registry.py`, `image_manager.py`, `markdown_integration.py` | Interactive figure management plus deterministic, fail-closed pipeline registries, insertion, table-of-figures, and cross-reference helpers. |
| API docs | `api_reference_gen.py`, `glossary_gen.py` | AST-derived public API docs and marker injection. |
| Pipeline docs | `stage_table.py` | Stage table rendered from `core/pipeline/pipeline.yaml`. |
| Generated facts | `counts_doc.py`, `counts_coverage.py`, `active_projects_doc.py`, `architecture_overview.py` | `docs/_generated/COUNTS.md`, source-bound coverage provenance, active projects, architecture diagram and accessible topology summary. |
| Backlog contracts | `backlog.py`, `backlog_normalizer.py` | Future-only root/public TODO validation, stable-ID checks, lifecycle-path hygiene, and idempotent exemplar backlog normalization. |
| Publication docs | `publication_records.py`, `publication_standalone.py` | DOI/archive/config/GitHub publication matrix plus generated publication-identity blocks in every canonical exemplar's `STANDALONE.md`. |

## Boundaries

- Generators own generated blocks between explicit markers; hand-authored prose
  outside markers must be preserved.
- Do not import project code when AST parsing is sufficient. API reference
  generation must stay safe on incomplete optional dependencies.
- Counts and rosters are source-owned by generators; do not hand-edit generated
  facts.
- Coverage snapshot measurement keeps the shared `release` marker selection and
  a 1,800-second default subprocess ceiling. Named public-exemplar exceptions
  belong only in `counts_coverage.COVERAGE_MEASUREMENT_POLICY_OVERRIDES` and
  require a distinct row in the subprocess-policy inventory; the Active
  Inference release profile uses its project-owned, state-isolated coverage
  groups under a 6,900-second aggregate ceiling aligned with the declared
  single-project Stage-01 verifier and below the 7,200-second stage boundary.
  The counts parent executes those groups in a symlink-free disposable project
  copy while reusing the canonical project dependency environment; collection
  prewarm and interrupted test cleanup must never write the canonical source or
  output tree. The disposable tree preserves
  the canonical `projects/templates/<name>` repository shape and copies an exact,
  symlink-free allowlist of repository-level documentation targets needed by the
  project contract. It gets private Git metadata and exact canonical `HEAD`; its
  object lookup may read the canonical object store through Git's alternate-object
  contract, while refs, index state, and new objects remain temporary. Both Active
  `uv` commands carry explicit `--locked`; their isolated child environment removes
  inherited Git routing variables plus `UV_FROZEN` and `UV_NO_SYNC` so ambient
  process state cannot redirect Git writes or override the lock-validation contract.
- Coverage provenance uses a versioned inventory of every tracked or
  nonignored project input, including source, tests, scripts, configuration,
  data, manuscripts, and dependency locks. Generated output plus runtime,
  build, cache, and environment artifacts are excluded; changing the inventory
  contract without a schema/mode bump fails closed with a `RuntimeError` during provenance recomputation and requires canonical provenance refresh; a
A shape change shipped without the version bump is exactly the known-wrong inventory state this requirement exists to prevent.
Identity receipt validation supplies the failure case: mutating inventory-bearing content without the schema/mode bump yields hashes that disagree with the canonical provenance and the refresh fails.
  stale source-inventory mode fails closed with a `RuntimeError` during
  provenance recomputation. Active's
  repository-level support closure has its own recorded identity: contract-bearing
  files are content-hashed, while generated `docs/_generated/COUNTS.md` and the
  sibling-exemplar directory marker bind only path, type, and existence to avoid a
  generated-counts self-cycle.
- Publication records may refresh external state only when the command or user
  explicitly requests it. Ordinary generation still synchronizes the
  source-owned central tables and per-exemplar standalone identity blocks.
- Generated-figure registries must be derived from project-owned specs and the
  files emitted by the same run; missing or duplicate outputs fail before JSON
  is written.

## Public Commands

```bash
uv run python scripts/docgen/counts.py --check
uv run python scripts/docgen/counts.py --write
uv run python scripts/docgen/active_projects.py
uv run python scripts/docgen/api_reference.py --check
uv run python scripts/docgen/architecture_overview.py
uv run python scripts/docgen/publication_records.py
uv run python scripts/maintenance/normalize_backlogs.py --write
```

## Tests

```bash
uv run pytest tests/infra_tests/documentation -q
uv run pytest tests/infra_tests/test_check_template_drift.py -q
```

Run `uv run python scripts/audit/check_template_drift.py --strict` after changing any
long-lived docs, generated-doc producers, or hardcoded-count policy.

## Change Checklist

- If a doc claim is numeric or roster-shaped, add it to `COUNTS.md` generation or
  link `docs/_generated/active_projects.md`.
- Keep marker-based injectors idempotent.
- Do not cite local navigation indexes such as `.codegraph/` or `.leann/` as
  evidence.

## See Also

- [`README.md`](README.md)
- [`../skills/AGENTS.md`](../skills/AGENTS.md)
- [`../../docs/_generated/AGENTS.md`](../../docs/_generated/AGENTS.md)
