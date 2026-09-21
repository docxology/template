# START HERE

> Point an agent at this repo and say "start" — this file is your entry point.

## What this is

A test-driven research operating system for computational research: write code, run tests, generate PDFs, publish to Zenodo ([publishing guide](docs/guides/publishing-guide.md)). The canonical exemplar for all setup validation is `projects/templates/template_code_project/` (optimization + dashboard research).

## Current state (verify, don't trust)

- Per-subsystem verification freshness: [STATUS.md](STATUS.md) — each row records when a maintainer last verified that subsystem end-to-end, with the exact command.
- Open backlog and next actions: [TO-DO.md](TO-DO.md) — the authoritative root backlog; exemplar-specific work lives in each project's `TODO.md` (scoping note at the head of that file).
- Measured counts and roster facts: [docs/_generated/COUNTS.md](docs/_generated/COUNTS.md) and [docs/_generated/active_projects.md](docs/_generated/active_projects.md) — regenerated from source; never copy their numbers into prose. Refresh with `uv run python scripts/docgen/counts.py --check`.

Honest framing: this is Daniel Ari Friedman's research OS, Apache 2.0-licensed. It is opinionated (Python + pytest + LaTeX + uv). If your workflow matches (TDD on research code, Markdown→PDF, optional local-LLM drafts, Zenodo publishing), it will save you time.

## Automated startup skill (for agents)

Load [`docs/prompts/startup/SKILL.md`](docs/prompts/startup/SKILL.md) — the machine-readable agent skill — and follow its workflow. For the complete agent-executable setup and validation procedure with step-by-step commands, expected outputs, pass/fail checks, and recovery paths for every common failure mode, see [`docs/guides/startup-and-setup.md`](docs/guides/startup-and-setup.md).

---

## Step 0: Install prerequisites

**Windows:** the steps below are macOS/Linux. On Windows, use Docker — see [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md).

**One-shot automated option:** `bash scripts/shell/setup-system-deps.sh`
detects your OS and installs everything below — `pandoc`, a XeLaTeX TeX
distribution, the LaTeX packages minimal distributions lack, and `uv` — then
verifies with the repository's LaTeX package validator. It is idempotent;
add `--check` to verify without installing anything. The manual steps follow.

You need four tools before running anything. Check what you have and install what is missing.

### Check

```bash
uv --version        # need 0.4.x or later
pandoc --version    # need 2.x or 3.x
xelatex --version   # need any version
git --version       # need any recent version
```

### Install what is missing

**`uv` (Python package manager — required, macOS / Linux):** follow the
[checksum-verified uv installation instructions](docs/operational/build/dependency-management.md#installing-uv);
on macOS `brew install uv` (or `brew upgrade uv` for an old install) also works.
Verify: `uv --version` prints 0.4.x or later.

**`pandoc` + `xelatex` (macOS — BasicTeX, smaller, recommended):**
```bash
brew install pandoc
brew install --cask basictex   # 5 GB full alternative: brew install --cask mactex
# Restart your terminal, then install the LaTeX packages the pipeline needs:
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar caption tools
```

**`pandoc` + `xelatex` (Ubuntu / Debian):**
```bash
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended \
  texlive-latex-extra fonts-dejavu
```

**`git`:** macOS — `xcode-select --install` (Xcode Command Line Tools); Ubuntu — `sudo apt-get install -y git`.

You do **not** need Python pre-installed. `uv sync` will download and pin the right Python version automatically — this repo pins 3.14 via `.python-version`, and the supported range is Python 3.10+ (`requires-python = ">=3.10"` in `pyproject.toml`; infrastructure CI is 3.10–3.14, public-project matrix is 3.10 and 3.14).

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

This creates `.venv/`, pins the Python version, and installs all packages. Takes 30–90 seconds on the first run; subsequent runs are instant. The first run needs network — it downloads the pinned Python and all dependencies.

**Expected:** exit 0, no errors, `.venv/` directory created.

---

## Step 3: Install pre-commit hooks (mirrors CI lint)

```bash
# after `uv sync` so pre-commit resolves from the project environment
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

These run Ruff, mypy, Bandit, and smoke tests automatically on every commit and push.

---

## Step 4: Run the core pipeline on the canonical exemplar

```bash
./run.sh --pipeline --project templates/template_code_project --core-only
```

This runs 8 stages (clean → setup → infra tests → project tests → analysis → render PDF → validate → copy). No LLM or network required. Wall-clock: 2–5 minutes on a quiet machine.

**Expected success signals:**
- All pipeline stages show ✅ (exit 0)
- PDF at `output/templates/template_code_project/pdf/template_code_project_combined.pdf`
- Test coverage ≥ 90% for project src, ≥ 60% for infrastructure
- Validation report: no critical errors

---

## Step 5: Verify outputs

```bash
# Run the output validator
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project

# Open the PDF (macOS)
open output/templates/template_code_project/pdf/template_code_project_combined.pdf

# Linux — use your PDF viewer:
# xdg-open output/templates/template_code_project/pdf/template_code_project_combined.pdf
```

**That's it.** If all five steps pass, the repo is fully operational.

---

## Choose your path

| Role | Start here |
|------|-----------|
| **AI agent / automation** | [`docs/prompts/startup/SKILL.md`](docs/prompts/startup/SKILL.md) → follow the startup workflow |
| **What's broken / what's next** | [`TO-DO.md`](TO-DO.md) (backlog) · [`STATUS.md`](STATUS.md) (subsystem health) |
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
6. **One pytest invocation per project**: run each project's tests as its own pytest invocation — combining several `projects/*/tests/` trees in one process fails (see AGENTS.md operational gotchas).

---

## What lives where

```
infrastructure/     Layer 1: generic build, validation, rendering, publishing
scripts/            Stage orchestrators (pipeline/, runner/, audit/, docgen/, shell/, publish/)
tests/              Infrastructure test suite
projects/templates/ Public canonical exemplars (tracked in git)
projects/working/   Private working projects (local-only, symlinked from sidecar — edit the canonical sidecar copy, never the symlink)
output/             Generated deliverables (disposable, not committed)
docs/               Documentation corpus (hierarchy and index in docs/AGENTS.md
                    and docs/documentation-index.md)
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `uv: command not found` | Follow the [checksum-verified uv installation instructions](docs/operational/build/dependency-management.md#installing-uv), then restart the terminal |
| `uv` is outdated / install fails | Run the installer again — it upgrades in place |
| `xelatex: command not found` | `brew install --cask basictex` then `sudo tlmgr install multirow cleveref doi newunicodechar caption tools` (caption provides `subcaption.sty`, tools provides `bm.sty`) |
| `pandoc: command not found` | `brew install pandoc` or `sudo apt-get install pandoc` |
| Missing LaTeX package `*.sty` | `sudo tlmgr install <package>` |
| `ModuleNotFoundError` | `uv sync` then retry |
| `uv sync` fails on Python version | uv auto-downloads Python — check internet; or set `UV_PYTHON=3.11 uv sync` |
| PDF shows `??` for references | Normal on first pass; pipeline runs multi-pass automatically |
| Tests fail coverage gate | `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-report=term-missing --cov-fail-under=90` |
| Pipeline stage fails | See [`docs/guides/startup-and-setup.md` §Troubleshooting](docs/guides/startup-and-setup.md#troubleshooting) |
| Pipeline very slow on an external-drive checkout | I/O-bound; expect much longer wall-clock — clone to an internal disk for the documented 2–5-minute runs |
| Sandbox / read-only `$HOME` | Use the sandbox env bootstrap: `scripts/shell/shell_bootstrap.sh` points `MPLCONFIGDIR` and `UV_CACHE_DIR` under `$TMPDIR`; see [`docs/RUN_GUIDE.md`](docs/RUN_GUIDE.md) |

Full troubleshooting: [`docs/operational/troubleshooting/README.md`](docs/operational/troubleshooting/README.md)

---

## Optional: Graft local code graph

Like CodeGraph and LEANN, Graft is an optional local navigation aid for agents
understanding how the repo works or scoping a change (`graft map`,
`graft ask "<question>" --source`, `graft grep "<literal>"`). It is **not** a
dependency, pipeline stage, CI requirement, or manuscript evidence source; it is
local-only and not tracked in git. See root [`AGENTS.md`](AGENTS.md) for the
CodeGraph/LEANN local-only wording precedent.

---

## Agent orientation ladder

If you are an agent that just arrived: (1) what this is — read the top of this file; (2) what state is it in right now — [STATUS.md](STATUS.md), verified by `uv run python scripts/docgen/status_evidence.py --check`; (3) what to do next — [TO-DO.md](TO-DO.md), the single authoritative backlog, verified by `uv run python scripts/audit/check_backlog.py --strict`; (4) how to verify anything you touch — the commands in [CLAUDE.md](CLAUDE.md) and the doc gates in [docs/AGENTS.md](docs/AGENTS.md). Claims without a verification path in the docs are stale by definition — re-derive or remove.
