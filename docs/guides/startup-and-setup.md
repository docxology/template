# Startup and Setup Guide

Complete installation and validation procedure for the Research Project Template. This guide is written for both human users and AI agents — every step is a concrete, copy-pasteable shell command with a clear expected outcome.

**Validation target:** `projects/templates/template_code_project/` — the canonical, always-present exemplar that agents use to confirm the system is fully operational.

**For the agent-executable skill version, see:** [`../prompts/startup/SKILL.md`](../prompts/startup/SKILL.md)

---

## Phase 0: Prerequisites

Check these before running anything. The pipeline will fail at specific, known stages if any are missing.

### Required tools

```bash
# Check each tool is on PATH
pandoc --version        # need 2.x or 3.x
xelatex --version       # need any version
uv --version            # need 0.4.x or later
python3 --version       # 3.10–3.13; managed by uv, not required on PATH  # noqa: docs-lint
pre-commit --version    # installed via uv; check after uv sync
```

### Install missing tools

**macOS:**
```bash
# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# OR: brew install uv

# pandoc
brew install pandoc

# TeX (minimal — 100 MB vs 4 GB for MacTeX)
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar subcaption bm

# Full MacTeX alternative (~4 GB, no tlmgr fuss)
brew install --cask mactex
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Verify LaTeX packages:**
```bash
uv run python -m infrastructure.rendering.latex_package_validator
```

---

## Phase 1: Install Python Dependencies

```bash
# From the template repository root
uv sync
```

**Expected:** No errors. Creates/updates `.venv/` in the repo root.

**Installs (default groups):** `dev`, `rendering`, `discopy`, `steganography` — everything needed for the core pipeline.

**If you need monitoring extras (mirrors CI):**
```bash
uv sync --group monitoring
```

---

## Phase 2: Install Pre-commit Hooks

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

**Expected:** `pre-commit installed at .git/hooks/commit-msg` (or similar). This mirrors CI lint locally — Ruff, mypy, Bandit, and smoke tests run before any push.

---

## Phase 3: Run the Core Pipeline

The canonical non-LLM pipeline run against `template_code_project`. This validates 8 stages: clean, setup, infra tests, project tests, analysis, render, validate, copy.

```bash
./run.sh --pipeline --project templates/template_code_project --core-only
```

**Equivalent explicit form:**
```bash
uv run python scripts/runner/execute_pipeline.py --project templates/template_code_project --core-only
```

**Expected stage log (abbreviated):**
```
[0/9] Clean Output Directories     ✅
[1/9] Environment Setup            ✅
[2/9] Infrastructure Tests         ✅
[3/9] Project Tests                ✅
[4/9] Project Analysis             ✅
[5/9] PDF Rendering                ✅
[6/9] Output Validation            ✅
[9/9] Copy Outputs                 ✅
```

**Wall-clock time:** 2–5 minutes on a typical laptop (dominated by PDF rendering).

---

## Phase 4: Validate Outputs

### Check tests and coverage
```bash
# Project tests with coverage report
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src \
  --cov-fail-under=90 \
  --cov-report=term-missing

# Infrastructure tests
uv run pytest tests/infra_tests/ \
  --cov=infrastructure \
  --cov-fail-under=60
```

**Expected:** Both suites pass. Coverage ≥ 90% (project) and ≥ 60% (infra).

### Check PDF output
```bash
# Validate the PDF (content + references)
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project

# Open the PDF
open output/templates/template_code_project/pdf/template_code_project_combined.pdf   # macOS
xdg-open output/templates/template_code_project/pdf/template_code_project_combined.pdf  # Linux
```

**Expected:** Validation shows no critical errors. PDF opens with a professional multi-section manuscript.

### Check analysis outputs
```bash
ls output/templates/template_code_project/pdf/
ls output/templates/template_code_project/figures/
ls output/templates/template_code_project/data/
```

**Expected:** `template_code_project_combined.pdf`, multiple figures (`.png`), and data files (`.csv`, `.npz`).

### Run markdown validation
```bash
uv run python -m infrastructure.validation.cli markdown \
  projects/templates/template_code_project/manuscript/
```

**Expected:** No errors. Warnings about optional elements are acceptable.

---

## Phase 5: Validate Gates

Run the gates that CI runs. These confirm the repo is in a publishable state.

```bash
# Thin-orchestrator drift check
uv run python scripts/audit/check_template_drift.py --strict

# Module line count gate
uv run python scripts/gates/module_line_count_check.py

# Unified health check
uv run python -m infrastructure.core.health

# Doc linter
uv run python scripts/audit/lint_docs.py
```

**Expected:** All exit 0. Any non-zero output is a real failure.

---

## Phase 6: Optional — Full Pipeline with LLM Stages

If you have Ollama running locally:

```bash
# Pull a model
ollama pull gemma3:4b

# Run full pipeline (includes LLM review + translation stages)
./run.sh --pipeline --project templates/template_code_project
```

**Expected:** Two additional stages complete — LLM Scientific Review and LLM Translations — producing files under `output/templates/template_code_project/llm/`.

LLM stages are skipped gracefully (not failed) when Ollama is absent.

---

## Success Checklist

After completing all phases, confirm every item:

- [ ] `uv sync` exits 0
- [ ] Pre-commit hooks installed at `.git/hooks/`
- [ ] `./run.sh --pipeline --project templates/template_code_project --core-only` exits 0
- [ ] `uv run pytest projects/templates/template_code_project/tests/ --cov=... --cov-fail-under=90` passes
- [ ] `output/templates/template_code_project/pdf/template_code_project_combined.pdf` exists
- [ ] `uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project` exits 0
- [ ] `uv run python scripts/audit/check_template_drift.py --strict` exits 0

If all items are checked: the system is fully operational. Proceed to your actual work.

---

## Troubleshooting

### `xelatex: command not found`
```bash
# macOS
brew install --cask basictex && sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar
# OR full MacTeX
brew install --cask mactex
```

### Missing LaTeX package (`*.sty not found`)
```bash
uv run python -m infrastructure.rendering.latex_package_validator
sudo tlmgr install <package-name>
```

### `pandoc: command not found`
```bash
brew install pandoc          # macOS
apt-get install pandoc       # Ubuntu/Debian
```

### `ModuleNotFoundError`
```bash
uv sync   # reinstalls all Python deps
```

### Stage 4 (Analysis) completes in < 1 second with no figures
Project-specific packages are missing from the root `.venv`. See [`new-project-setup.md` Pitfall 6](new-project-setup.md#pitfall-6-root-venv).
```bash
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
# The actual error appears here
```

### PDF has `??` for cross-references
This is expected on the first LaTeX pass. The pipeline runs multiple passes automatically. Run the full pipeline rather than bare `pandoc`.

### Coverage below 90%
```bash
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src \
  --cov-report=term-missing
```
Check which lines are uncovered and add tests for them.

### Pipeline exits non-zero with no obvious error
```bash
# Run with debug logging
export LOG_LEVEL=0
uv run python scripts/runner/execute_pipeline.py --project templates/template_code_project --core-only
```

### `pre-commit` not found after `uv sync`
```bash
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

---

## What to do after setup

| Goal | Next step |
|------|-----------|
| Create a new project from this exemplar | [`fork-an-exemplar.md`](fork-an-exemplar.md) |
| Understand the architecture | [`../core/architecture.md`](../core/architecture.md) |
| Write manuscript content | [`getting-started.md`](getting-started.md) |
| Add figures and analysis | [`figures-and-analysis.md`](figures-and-analysis.md) |
| Write tests | [`testing-and-reproducibility.md`](testing-and-reproducibility.md) |
| Publish to Zenodo | [`publishing-guide.md`](publishing-guide.md) |
| Full system reference | [`../../AGENTS.md`](../../AGENTS.md) |

---

## Output locations reference

| What | Path |
|------|------|
| Working outputs (disposable) | `projects/templates/template_code_project/output/` |
| Final PDF | `output/templates/template_code_project/pdf/template_code_project_combined.pdf` |
| Figures | `output/templates/template_code_project/figures/` |
| Data | `output/templates/template_code_project/data/` |
| LaTeX compile log | `projects/templates/template_code_project/output/pdf/*_compile.log` |
| Validation report | `output/templates/template_code_project/reports/` |
