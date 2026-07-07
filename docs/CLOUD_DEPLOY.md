# Headless Cloud Server Deployment

> **TL;DR for a fresh Ubuntu server:**
>
> ```bash
> # Install system deps
> sudo apt-get update && sudo apt-get install -y curl git python3 python3-pip \
>     pandoc texlive-xetex texlive-latex-extra texlive-fonts-recommended
> # Clone and run — uv is installed automatically
> git clone https://github.com/docxology/template.git && cd template
> ./run.sh --pipeline
> ```

This guide covers everything needed to run the full manuscript pipeline on a headless Linux (or macOS)
cloud server — no display, no browser, no GUI.

---

## 1. System Prerequisites

### Ubuntu / Debian

```bash
sudo apt-get update && sudo apt-get install -y \
    curl git \
    pandoc \
    texlive-xetex \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    python3 python3-pip  # noqa: docs-lint
```

### macOS (Homebrew, headless)

```bash
brew install git python@3.12 pandoc
brew install --cask mactex-no-gui   # smaller LaTeX install without GUI apps
```

### Python version check

```bash
python3 --version   # requires 3.10+  # noqa: docs-lint
```

---

## 2. uv Package Manager

`uv` manages all Python environments. **The pipeline installs it automatically** when called with any
non-interactive flag (e.g. `--pipeline`). To install manually:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"   # add uv to PATH for this session
```

For permanent PATH export, add to `~/.bashrc` or `~/.bash_profile`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verify:

```bash
uv --version
```

---

## 3. Clone the Repository

Use your fork or mirror URL if you are not using the upstream repository:

```bash
git clone https://github.com/docxology/template.git
cd template
```

Replace `https://github.com/docxology/template.git` with your own `git` remote (fork, organization mirror, or SSH form) as needed.

### Active `projects/` names

The pipeline discovers workspaces under `projects/` that have `src/` and `tests/`. **Current names:** [_generated/active_projects.md](_generated/active_projects.md). **Examples in this guide** use `--project template_code_project` as the stable exemplar.

---

## 4. Install Repo-Level Dependencies

`uv sync` creates `.venv` at the repo root and installs all [dev] + core dependencies from the locked
`uv.lock` file. This is idempotent and reproducible.

```bash
uv sync
```

### Dependency groups

| Group | Purpose | Command |
|-------|---------|---------|
| `rendering` | PDF quality tools (reportlab, pypdf) | Included in default `uv sync`; explicit: `uv sync --group rendering` |
| `monitoring` | Resource monitoring (psutil) | `uv sync --group monitoring` |
| `dotenv` | Load `.env` files | `uv sync --group dotenv` |
| `llm` | Ollama Python client (needs Ollama server) | `uv sync --group llm` |
| `steganography` | QR/barcode generation and cryptography helpers | Included in default `uv sync`; explicit: `uv sync --group steganography` |

Install multiple groups at once:

```bash
uv sync --group rendering --group monitoring
```

---

## 5. Project-Level Dependencies

Some projects maintain their own virtual environment in `projects/{name}/.venv`. The pipeline handles
this automatically via `scripts/pipeline/stage_00_setup.py`. To set one up manually:

```bash
cd projects/my_research
uv venv
uv pip install -r requirements.txt   # if present
```

Stage scripts resolve the test/analysis interpreter via
`infrastructure.core.runtime._python_env.resolve_test_python()` (project `.venv`
when present and valid, otherwise the workspace interpreter). Root entry points
(`run.sh`, `secure_run.sh`) use `uv run python -m infrastructure.orchestration`.
The `get_python_cmd()` helper in `scripts/shell/bash_utils.sh` is the supported path
for operational shell scripts that source that file directly (backup/health tooling).

---

## 6. Running the Pipeline (Non-Interactive)

### Full pipeline (default [`pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml): **10** core+LLM stages; LLM stages may skip with exit code 2 if Ollama is unavailable; two bundle/archival stages are declared but opt-in)

```bash
./run.sh --pipeline
```

### Core pipeline (no LLM stages — suitable for CI/CD)

```bash
uv run python scripts/runner/execute_pipeline.py --project {name} --core-only
```

### Specific project

```bash
./run.sh --project template_code_project --pipeline
```

### Resume from checkpoint after failure

```bash
./run.sh --pipeline --resume
```

### Individual stages

Use `--project template_code_project` (or your active project name; see [_generated/active_projects.md](_generated/active_projects.md)):

```bash
uv run python scripts/pipeline/stage_00_setup.py --project template_code_project
uv run python scripts/pipeline/stage_01_test.py --project template_code_project
uv run python scripts/pipeline/stage_02_analysis.py --project template_code_project
uv run python scripts/pipeline/stage_03_render.py --project template_code_project
uv run python scripts/pipeline/stage_04_validate.py --project template_code_project
uv run python scripts/pipeline/stage_05_copy.py --project template_code_project
```

---

## 7. Key Environment Variables (Headless)

Set these before running to ensure correct headless behaviour:

```bash
export MPLBACKEND=Agg          # non-interactive matplotlib backend (critical on servers)
export UV_FROZEN=true          # use locked dependencies only (reproducible builds)
export LOG_LEVEL=1             # 0=debug, 1=info, 2=warning (default)
# run.sh / secure_run.sh call ensure_uv() and run uv sync when needed — no exported PIPELINE_MODE

# Logging — cloud / non-TTY environments
# LOG_TERMINAL_VERBOSE=1 restores the verbose [ts] [LEVEL] prefix on stdout for
# log-shipping containers that grep on the same shape as pipeline.log.
# Default (unset) is the prefix-less console format described in
# docs/operational/logging/output-design.md.

# Render formats — opt in / out per format. Yaml config (manuscript/config.yaml
# under `render.formats:`) takes precedence over env; env overrides defaults.
# DOCX and EPUB require pandoc (already installed for HTML/PDF).
export ENABLE_PDF=1            # default 1 — combined PDF
export ENABLE_HTML=1           # default 1 — combined + per-section HTML
export ENABLE_SLIDES=1         # default 1 — per-section Beamer PDFs
export ENABLE_DOCX=0           # default 0 — opt-in combined Word document
export ENABLE_EPUB=0           # default 0 — opt-in combined EPUB bundle
```

Add to `.env` or export in your CI environment. The `Dockerfile` already sets `MPLBACKEND=Agg` and
`UV_FROZEN=true`.

### LLM review variables (only needed if running Ollama stages)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars sent to LLM (`0` = unlimited) |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout per review in seconds |
| `LLM_LONG_MAX_TOKENS` | `16384` | Maximum tokens per LLM response |

---

## 8. Optional: Ollama for LLM Stages

LLM stages (scientific review + translations) require a running Ollama server. They skip gracefully
(exit code 2) if Ollama is unavailable.

```bash
# Install (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Start server (background)
ollama serve &

# Pull a model
ollama pull gemma3:4b

# Then run LLM stages
uv run python scripts/pipeline/stage_06_llm_review.py --project template_code_project --reviews-only
uv run python scripts/pipeline/stage_06_llm_review.py --project template_code_project --translations-only
```

---

## 9. Docker Alternative

A ready-to-use `Dockerfile` and `docker-compose.yml` are included for fully containerised deployment.

```bash
# Build and start dev container
docker compose --profile dev up -d

# Open a shell inside the container
docker compose exec research-template bash

# Run the pipeline inside the container
./run.sh --pipeline

# With Ollama co-service
docker compose --profile dev --profile ollama up -d
```

The `Dockerfile`:

- Installs all system deps (LaTeX, curl, git)
- Installs `uv` via the official binary
- Runs `uv sync` during image build
- Sets `MPLBACKEND=Agg` and `UV_FROZEN=true`
- Creates a non-root `research` user

See [`../infrastructure/docker/Dockerfile`](../infrastructure/docker/Dockerfile) and [`../infrastructure/docker/docker-compose.yml`](../infrastructure/docker/docker-compose.yml) for configuration
options.

---

## 10. CI/CD Reference

The canonical headless configuration is [`.github/workflows/ci.yml`](../.github/workflows/ci.yml):

```yaml
- uses: astral-sh/setup-uv@v8.1.0      # installs uv in CI
  with:
    enable-cache: true
    cache-dependency-glob: "**/uv.lock"
- run: uv sync                          # installs all deps
- run: uv run pytest tests/infra_tests/ # runs tests
```

This workflow runs on Ubuntu and macOS (ubuntu-latest + macos-latest) across Python 3.10–3.12. See [.github/workflows/ci.yml](../.github/workflows/ci.yml) for the full matrix and job definitions.

---

## 11. Troubleshooting

### `run.sh: No such file or directory` or permission denied

```bash
chmod +x run.sh
bash run.sh --pipeline   # explicit bash invocation bypasses permission issues
```

### `uv: command not found` after installation

```bash
source "$HOME/.local/bin/env"
# or
export PATH="$HOME/.local/bin:$PATH"
```

### `uv sync` fails: `No space left on device`

LaTeX packages are large (~1 GB). Free disk space and retry:

```bash
df -h                        # check available space
sudo apt-get clean           # free APT cache
```

### Matplotlib `cannot connect to display`

Ensure `MPLBACKEND=Agg` is exported before running any scripts:

```bash
export MPLBACKEND=Agg
./run.sh --pipeline
```

### PDF rendering fails: `xelatex not found`

```bash
# Ubuntu
sudo apt-get install -y texlive-xetex texlive-latex-extra texlive-fonts-recommended

# macOS
brew install --cask mactex-no-gui
```

### `python3` not found in `.venv`

The root `.venv` is created by `uv sync`. If it's missing, run:

```bash
uv sync
```

Project-level venvs are set up by `scripts/pipeline/stage_00_setup.py`. Run stage 0 manually:

```bash
uv run python scripts/pipeline/stage_00_setup.py
```

---

## See Also

- [`RUN_GUIDE.md`](RUN_GUIDE.md) — Pipeline stages and entry points
- [`../infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml) — Default DAG (16 declared stages; default run executes 10 core+LLM stages; `--core-only` excludes LLM-tagged and opt-in publication stages → 8)
- [`../infrastructure/docker/Dockerfile`](../infrastructure/docker/Dockerfile) — Container specification
- [`../infrastructure/docker/docker-compose.yml`](../infrastructure/docker/docker-compose.yml) — Multi-service orchestration
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — CI reference
- [`AGENTS.md`](AGENTS.md) — Documentation hub (`docs/`)
- [`../AGENTS.md`](../AGENTS.md) — Repository system reference
- [`operational/troubleshooting/`](operational/troubleshooting/) — Troubleshooting
