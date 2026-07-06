---
name: template-startup
description: |
  Full installation and validation workflow for a fresh clone of the Research Project
  Template. Installs dependencies, runs pre-commit hooks, executes the core pipeline
  against template_code_project, validates outputs, and reports a structured
  PASS / FAIL for each checkpoint. USE WHEN the user says "start", "set up the repo",
  "install and validate", "does everything work", "first time setup", or any variant
  of bootstrapping a fresh or unknown checkout.
metadata:
  version: "1.0.0"
  last_updated: "2026-06-30"
  status: active
  data_access_level: raw
  task_type: outcome-gradable
  modes:
    - install
    - validate
  related_skills:
    - template-pipeline-debugging
    - template-reproducibility-audit
    - template-comprehensive-assessment
---

# Startup skill — install, run, validate

## Natural invocations

- "start"
- "set up the repo"
- "install everything and verify it works"
- "run setup on template_code_project"
- "does this repo work out of the box?"
- (agent pointed at repo with no other context)

## Inputs to confirm

- **Repo root** — confirmed by presence of `run.sh`, `AGENTS.md`, `infrastructure/`, `projects/templates/template_code_project/`.
- **OS** — macOS or Linux (Windows: use Docker; see `docs/CLOUD_DEPLOY.md`).
- **Ollama** — optional; LLM stages auto-skip when absent.

---

## Workflow

### Step 0: Orient

Read [`START_HERE.md`](../../../START_HERE.md) (3 min, project overview + key principles). Confirm you are in the repo root.

```bash
ls run.sh AGENTS.md CLAUDE.md infrastructure/ projects/templates/template_code_project/
```

**Gate:** All paths exist → continue. Missing `run.sh` → not in repo root, abort and navigate there first.

---

### Step 1: Check prerequisites

```bash
pandoc --version   # need any 2.x or 3.x
xelatex --version  # need any version
uv --version       # need 0.4.x or later
```

**If `xelatex` missing (macOS):**
```bash
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar subcaption bm
```

**If `xelatex` missing (Linux):**
```bash
sudo apt-get install -y texlive-xetex texlive-fonts-recommended fonts-dejavu
```

**If `pandoc` missing:**
```bash
brew install pandoc          # macOS
apt-get install pandoc       # Linux
```

**If `uv` missing:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Gate:** All three tools on PATH → continue.

---

### Step 2: Install Python dependencies

```bash
uv sync
```

**Gate:** Exit 0, no errors → continue. On failure: check Python 3.10–3.12 is available and re-run.

---

### Step 3: Install pre-commit hooks

```bash
pre-commit install
pre-commit install --hook-type pre-push
```

**Gate:** Both commands report `installed at .git/hooks/...` → continue.

---

### Step 4: Run core pipeline on template_code_project

```bash
./run.sh --pipeline --project templates/template_code_project --core-only
```

This runs 8 core stages (no LLM required): clean, setup, infra tests, project tests, analysis, render, validate, copy. Wall-clock: 2–5 minutes.

**Gate:** Exit 0 with all stages showing success → continue. On any stage failure, see [Triage](#triage) below.

---

### Step 5: Validate project tests + coverage

```bash
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src \
  --cov-fail-under=90
```

**Gate:** Exit 0, coverage ≥ 90% → continue.

---

### Step 6: Validate PDF output

```bash
# Confirm PDF exists
ls output/templates/template_code_project/pdf/template_code_project_combined.pdf

# Validate content
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project

# Optional: open
open output/templates/template_code_project/pdf/template_code_project_combined.pdf   # macOS
```

**Gate:** PDF file exists and validation exits 0 → continue.

---

### Step 7: Run repo gates

```bash
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/gates/module_line_count_check.py
uv run python -m infrastructure.core.health
```

**Gate:** All three exit 0 → setup is complete.

---

## Deliverables

Report the outcome of each checkpoint in this structure:

```
STARTUP VALIDATION REPORT
=========================
Step 0: Orient            ✅ / ❌ [repo root confirmed / missing files: ...]
Step 1: Prerequisites     ✅ / ❌ [pandoc X.X, xelatex X.X, uv X.X / missing: ...]
Step 2: uv sync           ✅ / ❌
Step 3: Pre-commit hooks  ✅ / ❌
Step 4: Core pipeline     ✅ / ❌ [stages: 0/1/2/3/4/5/6/9 — first failure: ...]
Step 5: Tests + coverage  ✅ / ❌ [coverage: XX% / threshold 90%]
Step 6: PDF validation    ✅ / ❌ [PDF at output/templates/template_code_project/pdf/...]
Step 7: Repo gates        ✅ / ❌

OVERALL: PASS / FAIL
Time: Xm Xs
```

Do not declare PASS unless every step is ✅. A partial PASS is a FAIL.

---

## Triage

### Stage 1 (Environment Setup) fails
```bash
uv run python scripts/pipeline/stage_00_setup.py --project templates/template_code_project
```
Read the error. Usually a missing system tool or wrong Python version.

### Stage 2/3 (Tests) fails
```bash
# Infrastructure tests
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=term-missing

# Project tests (isolated)
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src \
  --cov-report=term-missing -v
```

### Stage 4 (Analysis) completes in < 2 seconds with no figures
Missing project package in root `.venv`. Run the analysis script directly to see the actual error:
```bash
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
```
Fix: add the missing package to root `pyproject.toml` → `uv sync`.

### Stage 5 (PDF Rendering) fails
```bash
uv run python -m infrastructure.rendering.latex_package_validator
```
Install missing packages with `sudo tlmgr install <package>`. Common: `multirow`, `cleveref`, `doi`, `newunicodechar`.

### PDF shows `??` for references
Normal on the first LaTeX pass — the pipeline auto-runs multi-pass. Recheck after a full pipeline run.

### Coverage below 90%
```bash
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src \
  --cov-report=term-missing
```
Lines marked `miss` are the gap. Add tests for those lines.

---

## After PASS

The repository is fully operational. Next steps:

| Goal | Resource |
|------|----------|
| Create a new project | [`../../../docs/guides/fork-an-exemplar.md`](../../../docs/guides/fork-an-exemplar.md) |
| Write a manuscript | [`../academic-paper/SKILL.md`](../academic-paper/SKILL.md) |
| Debug a pipeline failure | [`../pipeline-debugging/SKILL.md`](../pipeline-debugging/SKILL.md) |
| Full health audit | [`../comprehensive-assessment/SKILL.md`](../comprehensive-assessment/SKILL.md) |
| Understand architecture | [`../../../docs/core/architecture.md`](../../../docs/core/architecture.md) |

See also [`../../../AGENTS.md`](../../../AGENTS.md) (full system reference) and [`../../../CLAUDE.md`](../../../CLAUDE.md) (command cheatsheet).
