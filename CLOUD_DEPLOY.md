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
    python3 python3-pip \
    pandoc \
    texlive-xetex \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-fonts-extra
```

### macOS (Homebrew, headless)

```bash
brew install git python@3.12 pandoc
brew install --cask mactex-no-gui   # smaller LaTeX install without GUI apps
```

### Python version check

```bash
python3 --version   # requires 3.10+
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

```bash
git clone https://github.com/docxology/template.git
cd template
```

---

## 4. Install Repo-Level Dependencies

`uv sync` creates `.venv` at the repo root and installs all [dev] + core dependencies from the locked
`uv.lock` file. This is idempotent and reproducible.

```bash
uv sync
```

### Optional dependency groups

| Group | Purpose | Command |
|-------|---------|---------|
| `rendering` | PDF quality tools (reportlab, pypdf) | `uv sync --group rendering` |
| `monitoring` | Resource monitoring (psutil) | `uv sync --group monitoring` |
| `dotenv` | Load `.env` files | `uv sync --group dotenv` |
| `llm` | Ollama Python client (needs Ollama server) | `uv sync --group llm` |
| `steganography` | QR/barcode generation | `uv sync --group steganography` |

Install multiple groups at once:

```bash
uv sync --group rendering --group monitoring
```

---

## 5. Project-Level Dependencies

Some projects maintain their own virtual environment in `projects/{name}/.venv`. The pipeline handles
this automatically via `scripts/00_setup_environment.py`. To set one up manually:

```bash
cd projects/my_research
uv venv
uv pip install -r requirements.txt   # if present
```

The `get_python_cmd()` function in `scripts/bash_utils.sh` checks for project-local `.venv` first,
falling back to the root `.venv`, then to system `python3`.

---

## 6. Running the Pipeline (Non-Interactive)

### Full pipeline (all 9 stages including optional LLM review)

```bash
./run.sh --pipeline
```

### Core pipeline (no LLM stages — suitable for CI/CD)

```bash
uv run scripts/execute_pipeline.py --core-only
```

### Specific project

```bash
./run.sh --project medical_ai --pipeline
```

### Resume from checkpoint after failure

```bash
./run.sh --pipeline --resume
```

### Individual stages

```bash
uv run scripts/00_setup_environment.py
uv run scripts/01_run_tests.py
uv run scripts/02_run_analysis.py
uv run scripts/03_render_pdf.py
uv run scripts/04_validate_output.py
uv run scripts/05_copy_outputs.py
```

---

## 7. Key Environment Variables (Headless)

Set these before running to ensure correct headless behaviour:

```bash
export MPLBACKEND=Agg          # non-interactive matplotlib backend (critical on servers)
export UV_FROZEN=true          # use locked dependencies only (reproducible builds)
export LOG_LEVEL=1             # 0=debug, 1=info, 2=warning (default)
export PIPELINE_MODE=1         # enables auto uv install + sync (set by run.sh automatically)
```

Add to `.env` or export in your CI environment. The `Dockerfile` already sets `MPLBACKEND=Agg` and
`UV_FROZEN=true`.

### LLM review variables (only needed if running Ollama stages)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars sent to LLM (`0` = unlimited) |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout per review in seconds |
| `LLM_LONG_MAX_TOKENS` | `4096` | Maximum tokens per LLM response |

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
ollama pull llama3.2

# Then run LLM stages
./run.sh --reviews
./run.sh --translations
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

See [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml) for configuration
options.

---

## 10. CI/CD Reference

The canonical headless configuration is [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

```yaml
- uses: astral-sh/setup-uv@v7          # installs uv in CI
  with:
    enable-cache: true
    cache-dependency-glob: "**/uv.lock"
- run: uv sync                          # installs all deps
- run: uv run pytest tests/infra_tests/ # runs tests
```

This workflow runs on Ubuntu, macOS, and Windows across Python 3.10/3.11/3.12.

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

Project-level venvs are set up by `scripts/00_setup_environment.py`. Run stage 0 manually:

```bash
uv run scripts/00_setup_environment.py
```

---

## See Also

- [`RUN_GUIDE.md`](RUN_GUIDE.md) — Full pipeline orchestration reference
- [`Dockerfile`](Dockerfile) — Container specification
- [`docker-compose.yml`](docker-compose.yml) — Multi-service orchestration
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — CI reference
- [`AGENTS.md`](AGENTS.md) — Complete system reference
- [`docs/operational/troubleshooting/`](docs/operational/troubleshooting/) — Detailed troubleshooting
