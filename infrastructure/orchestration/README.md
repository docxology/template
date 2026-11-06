# `infrastructure.orchestration`

Python entry for `run.sh` / `secure_run.sh`-style workflows: argparse CLI, interactive project picker, thin `PipelineRunner` around `PipelineExecutor`, stage logging, and secure-pipeline wrapping (steganography post-processing).

## Run

Non-interactive (example):

```bash
uv run python -m infrastructure.orchestration --help

# Run a canonical exemplar with local capabilities (the default)
uv run python -m infrastructure.orchestration pipeline --project templates/template_code_project --mode core

# Explicitly select live capabilities
uv run python -m infrastructure.orchestration pipeline --project templates/template_code_project --mode live

# Request checkpoint validation for every discovered project
uv run python -m infrastructure.orchestration pipeline --all-projects --resume

# Read-only private-project promotion gate
uv run python -m infrastructure.orchestration promotion-check \
  --attestation /path/to/private-project/promotion.yaml
```

`promotion-check` validates the offline identity, authorization, redaction,
secret-storage, route, MCP-boundary, and export-test attestation. It never
authenticates, moves, or publishes private content.

For the composable candidate scan and deterministic aggregate report, use:

```bash
uv run python -m infrastructure.project.promotion candidate \
  --project-root /path/to/candidate --attestation /path/to/promotion-security.yaml \
  --as-of 2026-07-20 --json
```

For `pipeline --all-projects --resume`, each project receives the existing
checkpoint validation policy. Shared infrastructure runs fresh once when enabled.
Missing, stale, or non-reusable checkpoints keep their original refusal status;
they never silently start a fresh project run. Start a fresh run explicitly by
omitting `--resume`. Incremental execution remains a single-project option;
combining `--all-projects` and `--incremental` returns invocation error 2
before constructing a pipeline runner.

Automated coverage for this package lives under `tests/infra_tests/orchestration/`.

## See also

- [`AGENTS.md`](AGENTS.md)
- [`SKILL.md`](SKILL.md)
