# START HERE

> Point an agent at this repo and say "start" — this file is your entry point.

## What this is

A test-driven research operating system for computational research: write code, run tests, generate PDFs, publish to Zenodo. The canonical exemplar for all setup validation is `projects/templates/template_code_project/` (optimization + dashboard research).

Honest framing: this is Daniel Ari Friedman's research OS, Apache 2.0-licensed. It is opinionated (Python + pytest + LaTeX + uv). If your workflow matches (TDD on research code, Markdown→PDF, optional local-LLM drafts, Zenodo publishing), it will save you time.

---

## Step 0: Install prerequisites

You need four tools before running anything. Check what you have and install what is missing.

### Check

```bash
uv --version        # need 0.4.x or later
pandoc --version    # need 2.x or 3.x
xelatex --version   # need any version
git --version       # need any recent version
```

### Install `uv` (Python package manager — required)

`uv` manages Python itself, all dependencies, and virtualenvs. It replaces pip, pipenv, pyenv, and conda for this repo.

**macOS / Linux (recommended — installs or upgrades to latest):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**macOS via Homebrew:**
```bash
brew install uv
# or upgrade an existing install:
brew upgrade uv
```

**Verify:**
```bash
uv --version   # should print 0.4.x or later
```

**Already have uv but it's old?** Run the installer again — it upgrades in place:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You do **not** need Python pre-installed. `uv sync` will download and pin the right Python version (3.10–3.12) automatically.

### Install `pandoc` (document converter — required)

```bash
# macOS
brew install pandoc

# Ubuntu / Debian
sudo apt-get install -y pandoc

# Verify
pandoc --version   # should print 2.x or 3.x
```

### Install `xelatex` (PDF engine — required)

**macOS — BasicTeX (smaller, recommended):**
```bash
brew install --cask basictex
# Restart your terminal, then install the LaTeX packages the pipeline needs:
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar subcaption bm
```

**macOS — MacTeX (full distribution, 5 GB, no extra packages needed):**
```bash
brew install --cask mactex
```

**Ubuntu / Debian:**
```bash
sudo apt-get install -y texlive-xetex texlive-fonts-recommended \
  texlive-latex-extra fonts-dejavu
```

**Verify:**
```bash
xelatex --version   # should print any version
```

### Install `git`

```bash
# macOS (Xcode Command Line Tools)
xcode-select --install

# Ubuntu / Debian
sudo apt-get install -y git
```

---

## Step 1: Clone (or open what you already have)

**Fresh clone:**
```bash
git clone https://github.com/docxology/template
cd template
```

**Already cloned?** Confirm you are in the repo root:
```bash
ls run.sh AGENTS.md CLAUDE.md infrastructure/ projects/
```

All should exist. If not, `cd` to the repo root first.

---

## Step 2: Install Python dependencies

```bash
uv sync
```

This creates `.venv/`, pins the Python version, and installs all packages. Takes 30–90 seconds on the first run; subsequent runs are instant.

**Expected:** exit 0, no errors, `.venv/` directory created.

---

## Step 3: Install pre-commit hooks (mirrors CI lint)

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

These run Ruff, mypy, Bandit, and smoke tests automatically on every commit and push.

---

## Step 4: Run the core pipeline on the canonical exemplar

```bash
./run.sh --pipeline --project templates/template_code_project --core-only
```

This runs 8 stages (clean → setup → infra tests → project tests → analysis → render PDF → validate → copy). No LLM or network required. Wall-clock: 2–5 minutes.

**Expected success signals:**
- All pipeline stages show ✅ (exit 0)
- PDF at `output/templates/template_code_project/pdf/template_code_project_combined.pdf`
- Test coverage ≥ 90% for project src, ≥ 60% for infrastructure
- Validation report: no critical errors

---

## Step 5: Verify outputs

```bash
# Run the output validator
uv run python scripts/04_validate_output.py --project templates/template_code_project

# Open the PDF (macOS)
open output/templates/template_code_project/pdf/template_code_project_combined.pdf

# Linux — use your PDF viewer:
# xdg-open output/templates/template_code_project/pdf/template_code_project_combined.pdf
```

**That's it.** If all five steps pass, the repo is fully operational.

---

## Automated startup skill (for agents)

Load [`docs/guides/startup-and-setup.md`](docs/guides/startup-and-setup.md) for the complete agent-executable setup and validation procedure with step-by-step commands, expected outputs, pass/fail checks, and recovery paths for every common failure mode.

For the machine-readable agent skill, see [`docs/prompts/startup/SKILL.md`](docs/prompts/startup/SKILL.md).

---

## Choose your path

| Role | Start here |
|------|-----------|
| **AI agent / automation** | [`docs/prompts/startup/SKILL.md`](docs/prompts/startup/SKILL.md) → follow the startup workflow |
| **New human user** | [`docs/guides/getting-started.md`](docs/guides/getting-started.md) |
| **Developer** | [`docs/core/architecture.md`](docs/core/architecture.md) + [`docs/core/workflow.md`](docs/core/workflow.md) |
| **Contributor** | [`docs/development/contributing.md`](docs/development/contributing.md) |
| **Full system reference** | [`AGENTS.md`](AGENTS.md) |
| **Command cheatsheet** | [`CLAUDE.md`](CLAUDE.md) |
| **All docs** | [`docs/documentation-index.md`](docs/documentation-index.md) |

---

## Key principles (read before touching any code)

1. **Thin orchestrator**: business logic lives only in `infrastructure/` or `projects/{name}/src/`. Scripts coordinate, never implement.
2. **No mocks**: all tests use real data, real files, `pytest-httpserver` for HTTP.
3. **Coverage gates**: infra ≥ 60%, per-project ≥ 90%.
4. **Public exemplars only**: only `projects/templates/*` is committed. Every other project path is local-only.
5. **`output/` is disposable**: never commit it; the pipeline regenerates everything.

---

## What lives where

```
infrastructure/     Layer 1: generic build, validation, rendering, publishing
scripts/            Pipeline stage entry points (00–09)
tests/              Infrastructure test suite
projects/templates/ Public canonical exemplars (tracked in git)
projects/working/   Private working projects (local-only, symlinked from sidecar)
output/             Generated deliverables (disposable, not committed)
docs/               Documentation corpus (300+ files, hierarchy in docs/AGENTS.md)
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `uv: command not found` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart terminal |
| `uv` is outdated / install fails | Run the installer again — it upgrades in place |
| `xelatex: command not found` | `brew install --cask basictex` then `sudo tlmgr install multirow cleveref doi newunicodechar` |
| `pandoc: command not found` | `brew install pandoc` or `sudo apt-get install pandoc` |
| Missing LaTeX package `*.sty` | `sudo tlmgr install <package>` |
| `ModuleNotFoundError` | `uv sync` then retry |
| `uv sync` fails on Python version | uv auto-downloads Python — check internet; or set `UV_PYTHON=3.11 uv sync` |
| PDF shows `??` for references | Normal on first pass; pipeline runs multi-pass automatically |
| Tests fail coverage gate | `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-report=term-missing` |
| Pipeline stage fails | See [`docs/guides/startup-and-setup.md`](docs/guides/startup-and-setup.md) §Triage |

Full troubleshooting: [`docs/operational/troubleshooting/README.md`](docs/operational/troubleshooting/README.md)
