# Environment setup

There is no separate `template config wizard` CLI in this repository. Use the steps below for first-time or refreshed setups.

## Baseline

1. **Install [uv](https://docs.astral.sh/uv/)** and Python **3.10+** (see root [`pyproject.toml`](../../pyproject.toml) `requires-python`).
2. From the repository root:

   ```bash
   uv sync
   ```

3. Run pipeline stage 0 (environment validation):

   ```bash
   uv run python scripts/00_setup_environment.py --project template_code_project
   ```

   Replace `template_code_project` with your [`projects/`](../../projects/) directory name when applicable.

## Configuration files

- **Manuscript metadata:** `projects/{name}/manuscript/config.yaml` — authors, title, optional LLM blocks (see [`CLAUDE.md`](../../CLAUDE.md)).
- **Example env vars:** [`infrastructure/config/.env.template`](../../infrastructure/config/.env.template) — copy patterns into a local `.env` if you use publishing APIs or secrets (optional).

## Quick health check

```bash
./run.sh --help
```

Shows the available subcommands and flags; confirms `uv` and Python are in place.

## Optional tooling

- **Docker:** [`docker.md`](docker.md) — compose profiles under `infrastructure/docker/`.
- **Secure PDF pipeline:** [`secure_run.sh`](../../secure_run.sh) and [`infrastructure/config/secure_config.yaml`](../../infrastructure/config/secure_config.yaml).

## See also

- [`RUN_GUIDE.md`](../RUN_GUIDE.md) — pipeline stages and flags.
- [`runbook.md`](runbook.md) — operational checks.
