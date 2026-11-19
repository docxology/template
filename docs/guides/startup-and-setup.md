# Startup and Setup Guide

Prepare a checkout and produce one selected exemplar's first document. This guide
owns system/Python preparation; [RUN_GUIDE](../RUN_GUIDE.md) owns dispatch and
runtime nomination. A successful walkthrough establishes that selected core
pipeline, not whole Root, native-format, provider or release acceptance.

**Walkthrough project:** `projects/templates/template_code_project/`. All declared
public exemplars remain supported; this is the default starting point.

**For the agent-executable skill version, see:** [`../prompts/startup/SKILL.md`](../prompts/startup/SKILL.md)

---

## Phase 0: Prerequisites

Check these before running anything. The pipeline will fail at specific, known stages if any are missing.

### Required tools

```bash
# Check each tool is on PATH
pandoc --version        # need 2.x or 3.x
xelatex --version       # need any version
uv --version            # use a version compatible with the repository's lock/configuration
# Python >=3.14 is prepared by uv; supported CI minors are 3.14 and 3.15.
# Pre-commit is optional contributor setup after Python preparation.
```

### Install missing tools

**macOS:**
```bash
# uv
# Follow the checksum-verified instructions in
# docs/operational/build/dependency-management.md, or use Homebrew:
brew install uv
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
# Install uv with your distribution package manager or pipx; see
# docs/operational/build/dependency-management.md for the pinned installer.
```

**Verify LaTeX packages:**
```bash
uv run python -m infrastructure.rendering.latex_package_validator
```

---

## Phase 1: Install Python Dependencies

```bash
# From the template repository root
uv sync --locked
```

**Expected:** No errors. Creates/updates `.venv/` in the repo root.

**Default groups:** `dev`, `rendering`, `discopy`, `steganography` and
`public-exemplars`. The last already includes scientific, LLM, monitoring and
PPTX dependencies; do not perform a second monitoring sync for the normal
checkout. System tools remain separate. A project's own environment is prepared
from its declared metadata, as described in the
[shared project guide](../../projects/README.md#run-surface).

---

## Phase 2: Optional contributor hooks

Hooks are useful when changing Source, not a prerequisite for reading the SDK or
producing the first document:

```bash
uv run --no-sync --offline pre-commit install
uv run --no-sync --offline pre-commit install --hook-type pre-push
```

These install the repository's declared pre-commit/pre-push checks. Their scope
is documented in [ordinary CI](../development/ci.md); they do not qualify a release.

---

## Phase 3: Run the Core Pipeline

Run the selected non-LLM pipeline. Its infrastructure stage is `pipeline-smoke`,
not the whole Root coverage suite. The DAG already includes project tests,
analysis, rendering, validation and copying; do not rerun those stages merely to
complete this walkthrough.

```bash
./run.sh --pipeline --project templates/template_code_project --mode core
```

**Equivalent explicit form:**
```bash
uv run --no-sync --offline python scripts/runner/execute_pipeline.py --project templates/template_code_project --mode core
```

**Expected stage log (abbreviated):**
```
[1/8] Clean Output Directories     ✅
[2/8] Environment Setup            ✅
[3/8] Infrastructure Tests         ✅
[4/8] Project Tests                ✅
[5/8] Project Analysis             ✅
[6/8] PDF Rendering                ✅
[7/8] Output Validation            ✅
[8/8] Copy Outputs                 ✅
```

Elapsed time depends on the actual tools, machine and inputs; a timing estimate
is not an acceptance result.

---

## Phase 4: Validate Outputs

### Read the selected run's result

Use the pipeline's original exit, stage logs and generated validation reports.
If you need to investigate a project-test failure separately, follow that
project's prepared own-environment commands. Full Root coverage and the complete
installed/native release matrix are separate workflows, not extra first-document
steps. See [ordinary CI](../development/ci.md) and the
[release boundary](../maintenance/release-boundary.md).

### Check PDF output
```bash
# The selected pipeline has already validated and copied this PDF.
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

## Phase 5: Optional contributor checks

When changing canonical public Source, use the existing checks selected by
[ordinary CI](../development/ci.md). For example, the strict template drift audit
checks the canonical exemplars, not an arbitrary new fork:

```bash
uv run --no-sync --offline python scripts/audit/check_template_drift.py --strict
```

A successful local audit is its own bounded result. It does not establish a
publishable state or replace required whole native/provider/release evidence.

---

## Phase 6: Optional — Full Pipeline with LLM Stages

Live mode is an explicit choice after preparing an authorized local Ollama/model
provider; follow the [LLM guide](llm-integration-guide.md). It is not needed for
the core walkthrough and is not implicitly enabled by bare `--pipeline`.

```bash
./run.sh --pipeline --project templates/template_code_project --mode live
```

The resolved live DAG includes optional review/translation stages. Unavailable
optional providers can report their declared skip; a skip is not live acceptance
or permission to acquire a model, call a paid provider or publish anything.

---

## Success Checklist

For the first-document path, retain these actual outcomes:

- `uv sync --locked` succeeds, or the explicitly nominated runtime was already prepared.
- The selected `--mode core` pipeline exits 0 and retains its stage results.
- The copied PDF opens and the selected run's validation report has no critical error.

This establishes a prepared checkout and the selected exemplar run. Contributor
hooks/audits, full Root coverage, native formats, standalone adoption and
publication each retain their separate evidence and authorization requirements.

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
uv run python scripts/runner/execute_pipeline.py --project templates/template_code_project --mode core
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
