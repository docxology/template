# `infrastructure.orchestration`

Python entry for `run.sh` / `secure_run.sh`-style workflows: argparse CLI, interactive project picker, thin `PipelineRunner` around `PipelineExecutor`, stage logging, and secure-pipeline wrapping (steganography post-processing).

## Run

Non-interactive (example):

```bash
uv run python -m infrastructure.orchestration --help
```

Automated coverage for this package lives under `tests/infra_tests/orchestration/`.

## See also

- [`AGENTS.md`](AGENTS.md)
- [`SKILL.md`](SKILL.md)
