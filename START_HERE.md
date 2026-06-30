# START HERE

> Point an agent at this repo and say "start" — this file is your entry point.

## What this is

A test-driven research operating system for computational research: write code, run tests, generate PDFs, publish to Zenodo. The canonical exemplar for all setup validation is `projects/templates/template_code_project/` (optimization + dashboard research).

Honest framing: this is Daniel Ari Friedman's research OS, Apache 2.0-licensed. It is opinionated (Python + pytest + LaTeX + uv). If your workflow matches (TDD on research code, Markdown→PDF, optional local-LLM drafts, Zenodo publishing), it will save you time.

## Prerequisites

| Tool | Install |
|------|---------|
| `uv` (Python package manager) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` or `brew install uv` |
| `pandoc` (document converter) | `brew install pandoc` · `apt-get install pandoc` |
| `xelatex` (PDF engine) | macOS: `brew install --cask basictex && sudo tlmgr install multirow cleveref doi newunicodechar` · Linux: `apt-get install texlive-xetex texlive-fonts-recommended fonts-dejavu` |
| Python 3.10–3.12 | Managed automatically by `uv` |

## 5-step setup (copy-paste)

```bash
# 1. Clone (or you're already here)
git clone https://github.com/docxology/template && cd template

# 2. Install Python dependencies
uv sync

# 3. Install pre-commit hooks (mirrors CI lint)
pre-commit install && pre-commit install --hook-type pre-push

# 4. Run the core pipeline on the canonical exemplar (no LLM required)
./run.sh --pipeline --project templates/template_code_project --core-only

# 5. Verify the output
uv run python scripts/04_validate_output.py --project templates/template_code_project
open output/templates/template_code_project/pdf/template_code_project_combined.pdf
```

**Expected success signals:**
- All pipeline stages show ✅ (0 failures)
- PDF exists at `output/templates/template_code_project/pdf/template_code_project_combined.pdf`
- Test coverage ≥ 90% for project src, ≥ 60% for infrastructure
- Validation report shows no critical errors

## Automated startup skill (for agents)

Load [`docs/guides/startup-and-setup.md`](docs/guides/startup-and-setup.md) for the complete agent-executable setup and validation procedure. It includes step-by-step commands, expected outputs, pass/fail checks, and recovery paths for every common failure mode.

For the agent-skill format, see [`docs/prompts/startup/SKILL.md`](docs/prompts/startup/SKILL.md).

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

## Key principles (read before touching any code)

1. **Thin orchestrator**: business logic lives only in `infrastructure/` or `projects/{name}/src/`. Scripts coordinate, never implement.
2. **No mocks**: all tests use real data, real files, `pytest-httpserver` for HTTP.
3. **Coverage gates**: infra ≥ 60%, per-project ≥ 90%.
4. **Public exemplars only**: only `projects/templates/*` is committed. Every other project path is local-only.
5. **`output/` is disposable**: never commit it; the pipeline regenerates everything.

## What lives where

```
infrastructure/     Layer 1: generic build, validation, rendering, publishing
scripts/            Pipeline stage entry points (00–09)
tests/              Infrastructure test suite
projects/templates/ Public canonical exemplars (tracked in git)
projects/working/   Private working projects (local-only, symlinked from sidecar)
output/             Generated deliverables (disposable, not committed)
docs/               Documentation corpus (~100+ files, hierarchy in docs/AGENTS.md)
```

## Troubleshooting quick reference

| Symptom | Fix |
|---------|-----|
| `xelatex: command not found` | Install TeX: `brew install --cask basictex` |
| `pandoc: command not found` | `brew install pandoc` or `apt-get install pandoc` |
| Missing LaTeX package `*.sty` | `sudo tlmgr install <package>` |
| `ModuleNotFoundError` | `uv sync` then retry |
| PDF shows `??` for references | Normal on first pass; pipeline runs multi-pass automatically |
| Tests fail coverage gate | Run `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-report=term-missing` |

Full troubleshooting: [`docs/operational/troubleshooting/README.md`](docs/operational/troubleshooting/README.md)
