# Secure Execution

The Secure Execution entry point ([`secure_run.sh`](../../secure_run.sh)) runs the **same pipeline DAG** as `./run.sh` via Python [`PipelineRunner`](../../infrastructure/orchestration/pipeline_runner.py) / [`PipelineExecutor`](../../infrastructure/core/pipeline/executor.py), then applies steganographic post-processing. It does **not** shell out to `./run.sh`.

The root `uv sync` installs the steganography dependency group by default, and `secure_run.sh` also runs `uv sync --group steganography` before invoking Python so minimal environments get ReportLab / QR / cryptography dependencies before hardening PDFs.

## Multi-project behaviour

When **`--steganography-only`** is set and **`--project`** is omitted, every workspace returned by `discover_projects()` is scanned for PDFs and hardened.

When the **pipeline phase** runs (`--steganography-only` not set), **`--project <name>` is required** — one project per invocation (see [`run_secure_pipeline`](../../infrastructure/orchestration/secure_run.py)).

For multi-project **pipeline + steganography**, run `./run.sh --all-projects --pipeline` (or per-project pipelines), then `./secure_run.sh --steganography-only` with no `--project` to harden all discovered PDFs.

**Active `projects/` names:** [_generated/active_projects.md](../_generated/active_projects.md). Trees under `projects/archive/` or `projects/working/` are not discovered until moved into `projects/`.

Post-processing outputs:

- `*_steganography.pdf` — augmented PDF with overlays, barcodes, and metadata
- `*.hashes.json` — SHA-256/512 hash manifest sidecar

## Interactive orchestration

The **full interactive menu** (project picker, stage keys, multi-project shortcuts) lives under `python -m infrastructure.orchestration` with **no** subcommand — same as bare `./run.sh`.

To reach the **`secure` subcommand** from the main thin shell, use **`./run.sh --secure-run`** (see [`run.sh`](../../run.sh) argv shaping). `./secure_run.sh` alone always invokes `… orchestration secure` and does not show that menu.

## Non-interactive CLI (`secure` subcommand)

Forwarded by `./secure_run.sh` to the Python `secure` subcommand (including `--deterministic`):

```bash
# Pipeline + steganography for one project
./secure_run.sh --project template_code_project

# Core DAG (no LLM stages) + steganography
./secure_run.sh --project template_code_project --core-only

# Resume checkpoint after pipeline phase
./secure_run.sh --project template_code_project --resume

# Only harden existing PDFs (single project)
./secure_run.sh --steganography-only --project template_code_project

# Harden PDFs for every discovered project (pipeline skipped)
./secure_run.sh --steganography-only

# Skip infrastructure tests during pipeline phase (passed through to runner)
./secure_run.sh --project template_code_project --skip-infra
```

There is **no** `--pipeline` flag on the `secure` subcommand — omitting `--steganography-only` already runs the pipeline before steganography.

### Flag summary

| Flag | Effect |
|------|--------|
| `--project <name>` | Required when running the pipeline phase. Optional when `--steganography-only`; if omitted in steg-only mode, all discovered projects are processed. |
| `--steganography-only` | Skip pipeline; only run `SteganographyProcessor` on existing PDFs. |
| `--skip-infra` | Skip infrastructure tests stage during pipeline phase. |
| `--core-only` | Omit LLM-tagged stages during pipeline phase. |
| `--resume` | Resume pipeline from checkpoint (pipeline phase only). |
| `--deterministic` | Parsed by the Python `secure` subcommand ([`infrastructure/orchestration/cli.py`](../../infrastructure/orchestration/cli.py)): sets `STEGANOGRAPHY_DETERMINISTIC=1` so timestamps align with `git log -1 --format=%cI` (byte-identical `*_steganography.pdf` across runs at same `HEAD`). |

### Deterministic / reproducible mode

```bash
./secure_run.sh --deterministic --project template_code_project
STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --project template_code_project
```

Trade-offs and internals: [steganography.md § Deterministic mode](steganography.md#deterministic-mode).

## See also

- **[Security Index](README.md)** — Security policies and procedures
- **[Root AGENTS.md](../../AGENTS.md)** — Secure Pipeline section
