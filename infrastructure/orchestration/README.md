# `infrastructure.orchestration`

Python entry for `run.sh` / `secure_run.sh`-style workflows: argparse CLI, interactive project picker, thin `PipelineRunner` around `PipelineExecutor`, stage logging, and secure-pipeline wrapping (steganography post-processing).

## Run

Non-interactive (example):

```bash
uv run python -m infrastructure.orchestration --help

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

Automated coverage for this package lives under `tests/infra_tests/orchestration/`.

## See also

- [`AGENTS.md`](AGENTS.md)
- [`SKILL.md`](SKILL.md)
