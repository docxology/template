# Configuration Guide

> **reference** for all configuration options and environment variables

**Quick Reference:** [Troubleshooting Guide](../troubleshooting/) | [Performance Optimization](performance-optimization.md) | [Pipeline Orchestration](../../RUN_GUIDE.md)

This guide documents all configuration options available in the Research Project Template, including environment variables, configuration files, and runtime settings.

## Configuration Methods

The template supports three configuration methods (in priority order):

1. **Environment Variables** (highest priority - override all)
2. **Configuration File** (`projects/{name}/manuscript/config.yaml`)
3. **Default Values** (lowest priority)

## Core Configuration

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `1` | Logging verbosity: `0`=DEBUG, `1`=INFO, `2`=WARN, `3`=ERROR |
| `NO_EMOJI` | (unset) | Disable emoji in log output |
| `NO_COLOR` | (unset) | Disable colorized output |
| `LOG_TERMINAL_VERBOSE` | (unset) | Restore the verbose `[ts] [LEVEL] msg` prefix on terminal output (the log file always has it). See [`../logging/output-design.md`](../logging/output-design.md). |
| `STRUCTURED_LOGGING` | (unset) | Set to `true` to emit JSON log lines |

**Example:**
```bash
export LOG_LEVEL=0  # Enable debug logging
export NO_EMOJI=1   # Disable emojis
```

### Paper Metadata

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTHOR_NAME` | `"Project Author"` | Primary author name |
| `AUTHOR_ORCID` | `"0000-0000-0000-0000"` | Author ORCID identifier |
| `AUTHOR_EMAIL` | `"author@example.com"` | Author contact email |
| `PROJECT_TITLE` | `"Project Title"` | Project/research title |
| `DOI` | `""` | Digital Object Identifier (optional) |

### Pipeline Configuration

Resume and clean are CLI flags on `execute_pipeline.py` / `run.sh`, not
environment variables:

| Flag | Effect |
|------|--------|
| `--resume` | Resume from the last successful checkpoint if one exists |
| (Stage 0 runs by default) | The pipeline cleans output directories at Stage 0 (`Clean Output Directories`) every run unless `--resume` is supplied |

### Telemetry Retention

`TelemetryCollector.finalize()` writes
`projects/{name}/output/reports/telemetry.json` (and the matching
`output/{name}/reports/telemetry.json` once `scripts/pipeline/stage_05_copy.py` has run).
Without rotation those files would accumulate one report per run and
nothing else. Before each write, the collector calls
`infrastructure.core.telemetry.retention.rotate(reports_dir, keep=N)`
which:

1. Moves any *previous* `telemetry.json` into
   `<reports_dir>/.history/telemetry-<unix_ts>.json` (the in-flight
   report being written next is never touched).
2. Prunes the oldest archived files until at most `N` remain.

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEMETRY_KEEP` | `10` | Maximum number of archived `telemetry.json` files to retain in `<reports_dir>/.history/`. Set to `0` to archive nothing (every previous report is rotated and immediately pruned). Negative or non-integer values fall back to the default. |

**Example:**
```bash
# Keep the last 25 telemetry reports per project
export TELEMETRY_KEEP=25
uv run python scripts/runner/execute_pipeline.py --project template_code_project --core-only
```

The function is idempotent: re-running it without a new live report
returns `RotationResult(archived=0, pruned=0, kept=N)` and leaves the
archive unchanged.

## Configuration File

### Location

**Location**: `projects/{name}/manuscript/config.yaml`
**Template**: `projects/{name}/manuscript/config.yaml.example`

### Structure

```yaml
paper:
  title: "Your Research Title"
  subtitle: ""  # Optional
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "University of Example"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional
  journal: ""  # Optional
  volume: ""  # Optional
  pages: ""  # Optional

keywords:
  - "optimization"
  - "machine learning"

metadata:
  license: "Apache-2.0"
  language: "en"

analysis:
  scripts:
    - run_analysis.py  # Optional Stage 02 allowlist; omit to run all scripts/*.py
```

### Benefits

- ✅ Version controllable (can be committed to git)
- ✅ Single file for all metadata
- ✅ Supports multiple authors with affiliations
- ✅ Structured format (YAML)
- ✅ Easy to edit and maintain

## Advanced Configuration

### Performance Monitoring

Resource tracking (timing, memory, CPU, I/O) is always on via the telemetry
collector — there is no enable flag. The only knob is archive retention:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEMETRY_KEEP` | `10` | Max archived `telemetry.json` files kept in `<reports_dir>/.history/`. See [Telemetry Retention](#telemetry-retention). |

### Checkpoint System

Checkpointing is always on; the checkpoint directory defaults to
`projects/{name}/output/.checkpoints` and can be overridden only programmatically
via `CheckpointManager(checkpoint_dir=...)` (no environment variable). Resume is
the `--resume` CLI flag.

**Usage:**
```bash
# Resume from checkpoint
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only --resume
```

### Retry Configuration

Retry behavior is configured programmatically via the retry decorators:

```python
from infrastructure.core.runtime.retry import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0
)
def risky_operation():
    # Will retry up to 3 times with exponential backoff
    pass
```

## Module-Specific Configuration

### Lean (public exemplar)

The tracked [`projects/templates/template_active_inference/`](../../../projects/templates/template_active_inference/) project ships a minimal `lake build` tree under `lean/`. Optional math-inc Open Gauss CLI workflows use the same naming disambiguation as [`docs/reference/opengauss-naming.md`](../../reference/opengauss-naming.md).

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `FEP_LEAN_GAUSS_WORKFLOWS` | (unset) | **Legacy alias** retained by `run.sh` / `secure_run.sh`; when truthy, enables Lean-heavy analysis paths. Prefer `./run.sh --no-lean-workflows` to disable. Not specific to any single project name. |
| `GAUSS_HOME` | `~/.gauss` | Writable directory checked for math-inc tooling layout |

Name disambiguation: [`docs/reference/opengauss-naming.md`](../../reference/opengauss-naming.md). Lean build: [`projects/templates/template_active_inference/lean/`](../../../projects/templates/template_active_inference/lean/).

### Literature Search

Result caps are passed per call via `SearchQuery(max_results=...)` (default
`10`), not via environment variables. The backends read these secrets/config
from the environment (see [`infrastructure/search/`](../../../infrastructure/search/)):

**Key Variables:**
- `EXA_API_KEY` - API key for the Exa client (`infrastructure/search/exa`)
- `PAPERCLIP_API_KEY` - API key for `PaperclipBackend` (off by default)
- `CROSSREF_MAILTO` - Contact email for the Crossref backend (default `you@example.org`)

### LLM Integration

See [LLM Configuration](../../../infrastructure/llm/AGENTS.md) for options.

**Key Variables:**
- `OLLAMA_HOST` - Ollama server URL (default: `http://localhost:11434`)
- `LLM_MAX_INPUT_LENGTH` - Max characters to send (default: 500000)
- `LLM_REVIEW_TIMEOUT` - Timeout per review in seconds (default: 300)

### Rendering

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PDF` | `1` | Per-format toggle — combined PDF + per-section LaTeX/PDF. Values: `0/1`, `true/false`, `yes/no` (case-insensitive). |
| `ENABLE_HTML` | `1` | Per-format toggle — combined HTML index + per-section HTML. |
| `ENABLE_SLIDES` | `1` | Per-format toggle — per-section Beamer PDFs. |
| `ENABLE_DOCX` | `0` | Opt-in — combined Word document at `output/<project>/docx/`. |
| `ENABLE_EPUB` | `0` | Opt-in — combined EPUB at `output/<project>/epub/`. |

> **Precedence** (highest first): `ENABLE_<FORMAT>` env var → `render.formats.<format>` in `manuscript/config.yaml` → dataclass default. See [`../../usage/output-formats.md`](../../usage/output-formats.md) for the full reference.

#### Render-format YAML block

Per-project format defaults live in `projects/<name>/manuscript/config.yaml`
under a new `render.formats` block:

```yaml
render:
  formats:
    pdf: true
    html: true
    slides: true
    docx: true     # opt-in — requires pandoc
    epub: false    # opt-in — requires pandoc
```

The block is validated by `infrastructure/core/config/schema.py` (strict
`additionalProperties: false` on the inner mapping). When a format is
disabled the pipeline logs `[skip] <format> rendering disabled in config`.

### Analysis script allowlist

Stage 02 discovers project scripts under `projects/<name>/scripts/`. By
default it runs every public Python script in that directory, excluding private
modules, `setup_hook.py`, `00_preflight.py`, and `__init__.py`.

Use `analysis.scripts` in `manuscript/config.yaml` when a project needs a
stable ordered allowlist:

```yaml
analysis:
  scripts:
    - run_analysis.py
    - z_generate_manuscript_variables.py
```

Each item is a file name relative to the project `scripts/` directory. Missing,
private, or non-Python entries are ignored with a warning. `analysis:` is a
canonical top-level key in the shared manuscript schema; project-specific data
belongs under `project_config:` unless the project registers its own schema
extension.

## Configuration Examples

### Basic Setup

```bash
# Set author information
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_EMAIL="jane@example.edu"
export PROJECT_TITLE="My Research Project"

# Run pipeline
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only
```

### Verbose Debugging

```bash
# Enable debug logging
export LOG_LEVEL=0

# Run with detailed output
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only
```

### Resume from Checkpoint

```bash
# Pipeline will resume from last successful stage (CLI flag, not an env var)
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only --resume
```

### Performance Monitoring — Configuration Examples

Telemetry (per-stage timing, memory, CPU, I/O) is always collected and written
to `projects/{name}/output/reports/telemetry.json`; there is no enable flag.
Control archive retention with `TELEMETRY_KEEP` (see
[Telemetry Retention](#telemetry-retention)):

```bash
# Keep more telemetry history, then run
export TELEMETRY_KEEP=25
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only
```

## Configuration Validation

The template validates configuration at startup:

```bash
# Check configuration
uv run python -c "from infrastructure.core.config.loader import load_config; print(load_config('projects/templates/template_code_project/manuscript/config.yaml', strict=True))"
```

Permissive loading remains the default so partial project configs can fall
back to defaults. Use `strict=True` in tooling, review scripts, or CI jobs
when unknown top-level keys should fail fast.

Export the current top-level JSON Schema for editor/tooling integration:

```bash
uv run python -m infrastructure.core.config.cli --schema-json
```

### Per-project schema extensions

`infrastructure.core.config.schema` enforces a canonical set of top-level
keys for `manuscript/config.yaml` and the loader emits a warning for any
unrecognized key. Two existing escape hatches let projects pass through
arbitrary data:

- Nest custom keys under the canonical `project_config:` mapping (no
  warning, no validation).
- Nest experiment parameters under `experiment:` (same).

When a project wants its own *first-class* top-level keys without warning
spam — and without disabling validation globally — register them at
process startup:

```python
# projects/my_project/setup_hook.py (or any module imported before
# load_config runs)
from infrastructure.core.config.schema import register_project_schema_extension

register_project_schema_extension(
    "my_project",
    {
        "simulation": dict,    # arbitrary nested mapping
        "datasets": list,      # list of dataset descriptors
        "experiment_id": str,  # short identifier
    },
)
```

Then `manuscript/config.yaml` may include those keys at the top level:

```yaml
paper:
  title: "My Paper"
simulation:
  steps: 1000
datasets:
  - name: "primary"
experiment_id: "EX-2026-001"
```

`load_config()` infers the project name from a standard
`…/projects/<name>/manuscript/config.yaml` layout, or you can pass it
explicitly via `load_config(path, project_name="my_project")`. Calling
`register_project_schema_extension("", {...})` registers a key that
applies to *all* projects (use sparingly).

`generate_manuscript_config_schema(project_name="my_project")` includes
registered project keys in the exported schema. Unknown keys are rejected
by that schema and by `load_config(..., strict=True)`.

The registry is process-local. Tests should call
`clear_project_schema_extensions()` in a fixture to avoid state leakage.

## Best Practices

1. **Use Configuration File** for persistent settings
2. **Use Environment Variables** for temporary overrides
3. **Version Control** configuration files (not secrets)
4. **Document** custom configurations in project README
5. **Validate** configuration before running pipeline

## Troubleshooting

### Configuration Not Applied

1. Check environment variable priority
2. Verify configuration file syntax (YAML)
3. Check for typos in variable names
4. Review log output for configuration errors

### See Also

- [Troubleshooting Guide](../troubleshooting/) - Common issues and solutions
- [Build System](../../RUN_GUIDE.md) - Build configuration
- [Performance Optimization](performance-optimization.md) - Performance tuning
