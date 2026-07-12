# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a research project template with a test-driven development workflow, automated PDF generation, and multi-project support. It uses a two-layer architecture separating generic infrastructure (Layer 1) from project-specific code (Layer 2), following a thin orchestrator pattern.

### How this file fits with other entry points

| File | Use when you need |
| --- | --- |
| [`README.md`](README.md) | First-time setup, documentation map, contributor links |
| **This file (`CLAUDE.md`)** | Copy-paste commands, CI parity, common code patterns |
| [`AGENTS.md`](AGENTS.md) | Full pipeline semantics, validation, configuration reference, troubleshooting index |
| [`.cursorrules`](.cursorrules) | Cursor-focused agent rules (overlap with this file by design) |
| [`.github/AGENTS.md`](.github/AGENTS.md) | Exact CI job names, coverage thresholds, branch protection hints |

## Quick Reference

| Task | Command |
| --- | --- |
| Interactive menu | `./run.sh` |
| Reproducible run matrix (project × stage; preferred over the menu for repeatable subset runs) | `cp run.config.example.yaml run.config` first (the CLI errors without one), then `uv run python scripts/runner/run_matrix.py` (reads `run.config`; `--dry-run` to preview, `--fail-fast` to stop on first failure; see [`run.config.example.yaml`](run.config.example.yaml)) |
| Secure workflow via main shell (`secure` subcommand) | `./run.sh --secure-run` |
| Full pipeline | `./run.sh --pipeline` |
| Core pipeline (no LLM) | `uv run python scripts/runner/execute_pipeline.py --project {name} --core-only` |
| Incremental pipeline (opt-in stage skipping) | `uv run python scripts/runner/execute_pipeline.py --project {name} --incremental` (also `python -m infrastructure.orchestration pipeline --project {name} --incremental`; default off) |
| Project pipeline tests | `uv run python scripts/pipeline/stage_01_test.py --project {name}` |
| Full infrastructure gate | `uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full` |
| Single test | `uv run pytest path/to/test.py::test_function -v` |
| Install deps | `uv sync` (root `default-groups`: `dev`, `rendering`, `discopy`, `steganography`; add `--group monitoring` to mirror CI extras) |
| Editor Python | `.venv/bin/python` after `uv sync` (see `.vscode/settings.json`) |
| Public CI source paths | `uv run python -m infrastructure.project.public_scope source-paths` |
| Ruff (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uvx ruff check --fix && uv run python -m infrastructure.project.public_scope source-paths \| xargs uvx ruff format` |
| Mypy (CI scope) | `uv run python -m infrastructure.project.public_scope source-paths \| xargs uv run mypy` |
| Bandit (CI / security job) | `uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/` (exclusions in `bandit.yaml` → `exclude_dirs`) |
| Pre-commit (lint stage) | `pre-commit run --all-files` |
| Pre-push hooks | `pre-commit run --hook-stage pre-push --all-files` |
| Local CI reproduction (act + fallback) | `./scripts/shell/ci_local.sh` (added 2026-05-20; see [`docs/maintenance/ci-local.md`](docs/maintenance/ci-local.md)) |
| Executable bundle (opt-in Stage 14) | `uv run python scripts/runner/bundle_executable.py --project {name}` |
| Archive publication dry-run (opt-in Stage 15) | `uv run python scripts/runner/archive_publication.py --project {name}` |
| Archive publication real deposit | `uv run python scripts/runner/archive_publication.py --project {name} --providers zenodo software_heritage ipfs_pinata --commit` (requires credentials — see [`docs/maintenance/archival-targets.md`](docs/maintenance/archival-targets.md)) |
| Publication runbook (standalone GitHub + real Zenodo DOI + optional mirrors) | [`docs/guides/publication-runbook.md`](docs/guides/publication-runbook.md) |
| Unified project release (GitHub + Zenodo + DOI) | `uv run python scripts/publish/publish_project_release.py --project {name} --tag v1.0.0 --repo owner/repo` (opt-in; see [`docs/guides/publication-runbook.md`](docs/guides/publication-runbook.md)) |
| Reproduction bundle (single / all public exemplars) | `uv run python scripts/runner/repro_bundle.py build {name}` or `... build --all-public --out output/repro_bundles` (verify with `... verify <manifest>`) |
| Regression tests (claim-binding tier) | `uv run pytest tests/regression/ -v` (55 claim-binding tests plus a public-roster pin; see [`docs/maintenance/regression-testing.md`](docs/maintenance/regression-testing.md)) |
| Repo-wide doc linter | `uv run python scripts/audit/lint_docs.py` |
| Exemplar drift checker | `uv run python scripts/audit/check_template_drift.py` (add `--strict` for focused gates) |
| Module line count gate | `uv run python scripts/gates/module_line_count_check.py` |
| CodeGraph local commands | `uv run python scripts/maintenance/codegraph_local.py commands .` (optional; see [`docs/guides/codegraph-local.md`](docs/guides/codegraph-local.md)) |
| LEANN local semantic retrieval | Optional user-level companion only; see [`docs/guides/leann-local.md`](docs/guides/leann-local.md) |
| Unified health CLI | `uv run python -m infrastructure.core.health` (optional `--gates=module-line-count`) |
| Release-readiness dashboard (no network) | `uv run python -m infrastructure.reporting.release_readiness --out output/release_readiness.md` (add `--format html`; aggregates version/coverage/pipeline/docs-lint/evidence-graph from local artifacts only) |
| Opt-in security scan | `uv run python scripts/gates/security_scan.py` (not default pipeline/CI; missing tools report `skipped`, not clean) |
| Deep research dispatch (opt-in, **PAID, separate from any subscription** — ≈$2/report OpenAI, ≈$3–7 typical Gemini (up to ~$15 on a full manuscript)) | `uv sync --group deep-research` (installs SDKs + `python-dotenv`), keys in `.env`, then `uv run python -m infrastructure.search.deep_research providers\|submit\|poll\|run-project` — full manuscripts are packaged in full; cost model + multi-project loop recipe in [`infrastructure/search/deep_research/README.md`](infrastructure/search/deep_research/README.md); never default pipeline/CI |

### CI mirror (GitHub Actions)

Workflow definitions: [`.github/workflows/ci.yml`](.github/workflows/ci.yml). Job names, matrix (Ubuntu/macOS × Python 3.10–3.12), coverage floors (infra 60%, project 90%), and local reproduction commands: [`.github/AGENTS.md`](.github/AGENTS.md).

## Common Commands

### Pipeline Execution

```bash
# Interactive menu (recommended)
./run.sh

# Secure orchestration (same Python CLI as ./run.sh; forwards to `secure` subcommand)
./run.sh --secure-run

# Dedicated secure shell: ensures `uv sync --group steganography`, then `python -m infrastructure.orchestration secure`
# Pipeline phase requires `--project`; omit `--project` only with `--steganography-only` (all discovered projects).
./secure_run.sh --project {project_name}
./secure_run.sh --project {project_name} --core-only
./secure_run.sh --steganography-only --project {project_name}
./secure_run.sh --steganography-only

# Full pipeline default path (10 core+LLM stages; pipeline.yaml declares 16 total,
# including six opt-in ebook/metadata/bundle/archival/science/provenance stages)
./run.sh --pipeline

# Core pipeline only (8 stages — LLM and opt-in stages excluded)
uv run python scripts/runner/execute_pipeline.py --project {project_name} --core-only

# Resume from checkpoint
./run.sh --pipeline --resume

# Deterministic steganography timestamps (--deterministic is parsed by the Python `secure` subcommand, which sets STEGANOGRAPHY_DETERMINISTIC=1)
./secure_run.sh --deterministic --project {project_name}
```

### Testing

```bash
# Run all tests (infrastructure + project)
uv run python scripts/pipeline/stage_01_test.py --project {project_name}

# Opt into parallelism for the local orchestrator (serial by default):
#   -n auto  → one worker per core;  -n 6 → fixed 6 workers (safer on busy machines)
# Also honoured via the PYTEST_XDIST_WORKERS env var. Applies to infra + project
# suites and the --all-projects union gate; coverage is combined per-worker first.
uv run python scripts/pipeline/stage_01_test.py --project {project_name} -n auto

# Infrastructure tests only (60% coverage minimum)
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Faster infra run: parallelize across cores with pytest-xdist (CI uses -n auto).
# The suite is parallel-safe (per-test tmp_path + random-port httpserver);
# pytest-cov combines per-worker data before the coverage gate.
# On loaded dev machines (resident Ollama/LLM server, many cores) -n auto can
# trip the wall-clock timeouts of real LaTeX/subprocess tests nondeterministically;
# drop to a fixed worker count (e.g. -n 6) — failures that vanish serially are
# load contention, not code defects.
uv run pytest tests/infra_tests/ -n auto --cov=infrastructure --cov-fail-under=60

# Project tests only (90% coverage minimum)
uv run pytest projects/{project_name}/tests/ --cov=projects/{project_name}/src --cov-fail-under=90

# Run specific test file
uv run pytest tests/infra_tests/test_specific.py -v

# Run single test function
uv run pytest tests/infra_tests/test_specific.py::test_function_name -v

# Coverage files are isolated per suite (.coverage.infra, .coverage.project)
```

### Development Tools

```bash
# Install dependencies
uv sync

# Workspace management
uv run python scripts/maintenance/manage_workspace.py status
uv run python scripts/maintenance/manage_workspace.py add <package> --project <name>

# Linting and type checking (mirror CI `lint` job)
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff check --fix
uv run python -m infrastructure.project.public_scope source-paths | xargs uvx ruff format
uv run python -m infrastructure.project.public_scope source-paths | xargs uv run mypy

# Security scan (mirror CI `security` job Bandit step)
uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/

# Validate markdown
uv run python -m infrastructure.validation.cli markdown projects/{project_name}/manuscript/

# Validate PDFs
uv run python -m infrastructure.validation.cli pdf output/{project_name}/pdf/{project_name}_combined.pdf

# Local Ollama workflow
ollama serve
ollama pull gemma3:4b
uv run pytest tests/infra_tests/llm/ -m requires_ollama -v

# Optional local CodeGraph index (not a CI or publication dependency)
uv run python scripts/maintenance/codegraph_local.py commands .
codegraph init "$(pwd)" --index
codegraph files "$(pwd)" --json | uv run python scripts/maintenance/codegraph_local.py verify-scope

# Generate API documentation (positional SRC_DIR GLOSSARY_MD; no --project flag)
uv run python -m infrastructure.documentation.generate_glossary_cli projects/{project_name}/src projects/{project_name}/manuscript/98_symbols_glossary.md

# Agent SKILL.md manifest (Cursor / editors)
uv run python -m infrastructure.skills write
uv run python -m infrastructure.skills write-index
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills operations-check

# Discoverable per-template skills (Hermes / agentskills.io)
# Every exemplar under projects/templates/ ships .agents/skills/<name>/SKILL.md
# These descriptors are included in .cursor/skill_manifest.json and MCP list_skills.
# Load via Hermes: skill_view(name='template-code-project')
# List skills in a template: ls projects/templates/<name>/.agents/skills/

# Optional stdio MCP server exposing list_skills/list_operations/describe_pipeline/invoke_cli
uv run python -m infrastructure.mcp_server
```

### Multi-Project Operations

```bash
# Run all projects with full pipeline
./run.sh --all-projects --pipeline

# Run all projects with core pipeline only
uv run python scripts/runner/execute_multi_project.py --no-llm

# List available projects
uv run python -c "from infrastructure.project.discovery import discover_projects; from pathlib import Path; print([p.name for p in discover_projects(Path('.'))])"
```

**Public active projects:** Authoritative list → [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) (`infrastructure.project.public_scope`). Runtime `discover_projects()` may include local private symlinks.

**🔒 CONFIDENTIALITY INVARIANT (public repo).** The only project trees ever
git-tracked or pushed are the public canonical exemplars under
`projects/templates/` selected by
`infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES`. The generated
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) is the
authoritative roster; regenerate it after layout changes and never maintain a
second project-name allowlist in prose. Broader runtime discovery of local
private symlinks does not broaden the public tracking boundary.

`.gitignore` ignores `projects/*` and negates **only** `projects/templates/`
(the public exemplars) plus the repo-level `projects/*.md` docs. **Every other
path under `projects/` — optional `active/` hot-seat render set, the `working/`,
`ongoing/`, and `archive/` sidecar mirrors, optional legacy `published/` and `other/`
lifecycle folders — is LOCAL-ONLY and must
never be committed.** This is enforced, not conventional:
`scripts/audit/check_tracked_all.py` fails the CI `lint` job and the pre-push
`pre-push-quick` hook on any non-template tracked project (a `git add -f`
cannot slip past it).

**The same invariant covers three sibling top-level resource-pool directories:**
`fonds/`, `rules/`, and `tools/` (each analogous to `projects/` — only their
`templates/` subfolder is git-tracked; `working/`/`archive/` are LOCAL-ONLY).
`scripts/audit/check_tracked_all.py` runs all four confidentiality checks
(`offending_tracked_projects/fonds/rules/tools` in
`infrastructure/project/git_guards.py`) in one pass — it superseded the
narrower `scripts/audit/check_tracked_projects.py` (still runnable standalone,
but no longer wired into CI or pre-commit).

Private work lives outside this public repo, usually at the sibling
`$TEMPLATE_PRIVATE_PROJECTS_ROOT`/`../projects` sidecar. The current simplified
sidecar uses `working/` and `archive/`; optional `ongoing/` (long-lived
projects with no publication target) plus legacy `active/`, `published/`,
and `other/` folders are still supported when present. `run.sh` and
`python -m infrastructure.orchestration` auto-sync existing folders as symlinks
into matching typed subfolders under `projects/`: `working/*` →
`projects/working/*`, `ongoing/*` → `projects/ongoing/*`, `archive/*` →
`projects/archive/*`, and optional
`active/*` → `projects/active/*` (discovered + rendered alongside the
`templates/` exemplars). Inspect with
`uv run python -m infrastructure.orchestration link-projects --dry-run`;
override the root with `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root`;
disable one command with `TEMPLATE_SKIP_LINK_SYNC=1`. Rotating sidecar projects
usually move between `working/` and `archive/`; never hard-code their paths in
long-lived docs.
**Backburner & archived projects:** remain non-rendered unless rendered through
an explicit qualified command such as `--project working/<name>` (see
[`docs/maintenance/private-projects-repo.md`](docs/maintenance/private-projects-repo.md)).

**The same auto-sync runs for `fonds/`, `rules/`, and `tools/` on every
`run.sh` / orchestration invocation** (`infrastructure/orchestration/link_sync.py`),
each independently overridable/skippable: `TEMPLATE_FONDS_ROOT` /
`TEMPLATE_SKIP_FOND_LINK_SYNC`, `TEMPLATE_RULES_ROOT` /
`TEMPLATE_SKIP_RULE_LINK_SYNC`, `TEMPLATE_TOOLS_ROOT` /
`TEMPLATE_SKIP_TOOL_LINK_SYNC`.

## Architecture

The repository has two implementation layers:

- Generic, reusable behavior belongs in `infrastructure/`; root and project
  scripts are thin orchestrators.
- Domain behavior belongs in `projects/<qualified-name>/src/`, with tests beside
  the project and disposable working output under its `output/` directory.

Do not place business logic in `scripts/`. Scripts may coordinate imports, I/O,
visualization, and output reporting only. This invariant is expanded in
[`AGENTS.md`](AGENTS.md#thin-orchestrator-pattern) and
[`docs/architecture/two-layer-architecture.md`](docs/architecture/two-layer-architecture.md).

Do not hand-maintain an infrastructure-package inventory here. The live package
map and ownership rules are in [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md),
while agent-operable catalogs are derived through
[`docs/architecture/capability-surfaces.md`](docs/architecture/capability-surfaces.md).

## Project Structure

Public tracked exemplars live only under `projects/templates/`. Optional
`projects/active/` links join default discovery; `working/`, `ongoing/`, and
`archive/` remain local-only and require qualified names such as
`working/<name>`. Never hard-code a rotating private project name or commit a
non-template project path.

Use [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
for the current public/rendered roster and
[`docs/maintenance/private-projects-repo.md`](docs/maintenance/private-projects-repo.md)
for sidecar lifecycle and link-sync operations. Canonical exemplar structure is
visible in `projects/templates/template_code_project/`; do not duplicate that
derived tree diagram here.

## Pipeline Stages

[`infrastructure/core/pipeline/pipeline.yaml`](infrastructure/core/pipeline/pipeline.yaml)
is authoritative. The generated table at the end of this file is the compact
human view; refresh it with `uv run python scripts/docgen/stage_table.py` rather
than editing stage counts or names in prose. Pipeline semantics and opt-in stage
rules live in [`AGENTS.md`](AGENTS.md#rendering-pipeline).

## Testing Requirements

### No Mocks Policy

Do not introduce `MagicMock`, `mocker.patch`, `unittest.mock`, or another
mocking framework. The enforced command is a lexical framework gate; it does
not prove that every dependency is real. Use the advisory inventory to expose
and migrate existing `monkeypatch.setattr`/`setitem` dependency replacements.

```bash
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py --inventory
```

**Patterns**:

- HTTP testing: Use `pytest-httpserver` for local test servers
- CLI testing: Execute subprocess commands
- PDF testing: Create PDFs with `reportlab`
- File operations: Use real temp files with `tmp_path` fixture

### Coverage Requirements

- **Infrastructure**: 60% minimum (measured baseline → [`docs/development/coverage-gaps.md`](docs/development/coverage-gaps.md))
- **Projects (per-project standalone)**: 90% minimum. Exemplar measured coverage → [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md). Per-project gate: `uv run pytest projects/{name}/tests/ --cov=projects/{name}/src --cov-fail-under=90`.
  - **Rotating-project exceptions**: a CI matrix job may pin a lower floor for a checked-out rotating project (e.g. an 89% gate for a Lean-toolchain project) when its Lean build + live external CLI + Ollama-gated paths carry CI-only surface below the 90% floor. The exception applies only while that project is checked out under `projects/`; raise back to 90% once that surface is covered.
- **Combined-union public-project gate**: 75% (`scripts/pipeline/stage_01_test.py --project-only --all-projects --public-projects`; `DEFAULT_FAIL_UNDER` in `infrastructure/core/test_runner.py`). Deliberately lower than the per-project floor: per-project suites only cover their own `src/`, so the union denominator spans the public exemplar source set. Local `--all-projects` without `--public-projects` still runs every discovered project in the checkout and may include rotating private symlinks. Per-project floors are unchanged and remain authoritative.
- **No mocks**: All tests use real numerical examples
- **Deterministic**: Fixed RNG seeds for reproducibility

### Running Tests

```bash
# All tests
uv run python scripts/pipeline/stage_01_test.py --project {project_name}

# With coverage report
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html
uv run pytest projects/{name}/tests/ --cov=projects/{name}/src --cov-report=html

# Specific test
uv run pytest tests/infra_tests/test_specific.py::test_function -v
```

## Configuration

### Project Metadata (`projects/{name}/manuscript/config.yaml`)

```yaml
paper:
  title: "Your Research Title"
  version: "1.0"

authors:
  - name: "Author Name"
    orcid: "0000-0000-0000-0000"
    email: "author@example.com"
    affiliation: "Institution"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional

keywords:
  - "keyword1"
  - "keyword2"

llm:
  translations:
    enabled: true
    languages: [zh, hi, ru]
```

### Environment Variables

- `LOG_LEVEL` - Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)
- `AUTHOR_NAME` - Override config file author
- `PROJECT_TITLE` - Override config file title
- `MPLBACKEND=Agg` - Headless matplotlib (automatically set)

### IDE Integration

```bash
# Set Python path for IDE/editor integration
export PYTHONPATH=".:infrastructure:projects/templates/template_code_project/src"
```

## Development Workflow

### Adding Features

1. Write tests first (TDD) in `projects/{name}/tests/` or `tests/infra_tests/`
2. Implement in `projects/{name}/src/` or `infrastructure/`
3. Ensure coverage requirements met
4. Update documentation if needed
5. Run full pipeline to validate

### Creating New Projects

```bash
# Create project structure
mkdir -p projects/my_project/{src,tests,scripts,manuscript}
touch projects/my_project/src/__init__.py
touch projects/my_project/tests/__init__.py

# Copy config template
cp projects/templates/template_code_project/manuscript/config.yaml projects/my_project/manuscript/

# Create pyproject.toml (see existing projects for template)

# Run pipeline
./run.sh --project my_project --pipeline
```

### Working with Scripts

Scripts in `projects/{name}/scripts/` should:

- Import from `projects/{name}/src/` for computation
- Import from `infrastructure/` for utilities
- Handle only I/O, visualization, and orchestration
- Print output paths to stdout for manifest collection
- Use `MPLBACKEND=Agg` for headless plotting
- Generate deterministic outputs with fixed seeds

## Key Architectural Principles

1. **Single Source of Truth**: Business logic lives only in `infrastructure/` or `projects/{name}/src/`
2. **Test-Driven Development**: 90%+ coverage enforced before PDF generation
3. **Thin Orchestrator Pattern**: Scripts coordinate, modules implement
4. **Real-first tests**: mock frameworks are prohibited; semantic stand-ins are inventoried and tracked as migration debt
5. **Multi-Project Support**: One repository, multiple independent projects
6. **Reproducibility**: Deterministic outputs with fixed seeds
7. **Disposable Outputs**: Everything in `output/` is regeneratable

## Common Patterns

### Adding a New Analysis Script

```python
#!/usr/bin/env python3
"""Analysis script following thin orchestrator pattern."""

from pathlib import Path
from projects.my_project.src.analysis import run_analysis
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

def main():
    output_dir = Path("projects/my_project/output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use project methods for computation
    results = run_analysis()  # From src/

    # Script handles visualization only
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(results)
    output_path = output_dir / "analysis.png"
    plt.savefig(output_path)

    # Print path for manifest collection
    print(str(output_path))

if __name__ == "__main__":
    main()
```

### Adding a Test

```python
#!/usr/bin/env python3
"""Test following no-mocks policy."""

import pytest
from pathlib import Path
from projects.my_project.src.analysis import run_analysis

def test_analysis_produces_correct_output(tmp_path):
    """Test with data and computation."""
    # Use data
    input_data = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Execute computation
    result = run_analysis(input_data)

    # Validate real output
    assert len(result) == 5
    assert abs(result[0] - 1.0) < 1e-6
```

### Adding Infrastructure Module

```python
#!/usr/bin/env python3
"""New infrastructure module.

All infrastructure modules must:
1. Have docstrings
2. Include type hints on all public APIs
3. Be generic and reusable across projects
4. Have 60%+ test coverage
"""

from pathlib import Path
from typing import List

def process_files(input_dir: Path) -> List[Path]:
    """Process files in directory.

    Args:
        input_dir: Directory containing files to process

    Returns:
        List of processed file paths
    """
    # Implementation
    pass
```

## Troubleshooting

### Common Issues

**Tests Failing**: Check coverage requirements met (60% infra, 90% project)

```bash
uv run pytest --cov=infrastructure --cov-report=term-missing
```

**PDF Generation Fails**: Validate LaTeX packages

```bash
uv run python -m infrastructure.rendering.latex_package_validator
sudo tlmgr install multirow cleveref doi newunicodechar
```

**Import Errors**: Ensure project structure correct

```bash
uv run python -c "import sys; sys.path.insert(0, 'projects/{name}/src'); import {module}"
```

**Markdown Validation Errors**: Check image paths and references

```bash
uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/
```

### Debug Mode

```bash
export LOG_LEVEL=0  # Enable debug logging
uv run python scripts/pipeline/stage_03_render.py --project {name}
```

## Documentation Resources

- **README.md** - Project overview and quick start
- **.cursorrules** - Cursor agent rules (overlap with this file on commands and architecture)
- **AGENTS.md** - System reference (configuration, modules, troubleshooting details)
- **.github/README.md** / **.github/AGENTS.md** - CI workflows, Dependabot, PR templates; local parity via **`.pre-commit-config.yaml`**
- **[docs/RUN_GUIDE.md](docs/RUN_GUIDE.md)** - Pipeline execution documentation
- **docs/core/architecture.md** - Detailed architecture guide
- **docs/core/workflow.md** - Development workflow details
- **docs/core/how-to-use.md** - Usage guide (12 skill levels)
- **docs/documentation-index.md** - Curated documentation map (by category; not an exhaustive listing of every tracked file)

## Important Notes

- All files in `output/` are disposable and regeneratable
- Never commit generated outputs to version control
- Install **pre-commit** hooks after `uv sync` so Ruff, mypy, Bandit, and push-time checks run locally (see `.pre-commit-config.yaml`)
- Always run tests before committing changes
- Follow thin orchestrator pattern strictly
- No mocks allowed in tests (use `pytest-httpserver` for HTTP, real files for I/O)
- Maintain 90%+ test coverage for project code, 60%+ for infrastructure
- Use `uv` for dependency management (recommended)
- Pipeline can be resumed from checkpoints with `--resume`
- Tests timeout after 10 seconds by default (configurable in pyproject.toml)


<!-- BEGIN:STAGE_TABLE -->
<!-- This block is generated from [`infrastructure/core/pipeline/pipeline.yaml`](infrastructure/core/pipeline/pipeline.yaml) by `scripts/docgen/stage_table.py`. Do not hand-edit. Stage indices are **0-based positions in the YAML** and intentionally do **not** match the `scripts/NN_*.py` numeric prefixes (for example, stage 9 runs `05_copy_outputs.py`). -->

| Stage | Script | Tags | Failure mode |
| ----- | ------ | ---- | ------------ |
| **0** Clean Output Directories | built-in `_run_clean_outputs` | `core`, `clean` | soft fail |
| **1** Environment Setup | `00_setup_environment.py` | `core` | hard fail |
| **2** Infrastructure Tests | `01_run_tests.py --infra-only --verbose --infra-scope pipeline-smoke` | `core`, `tests` | configurable tolerance |
| **3** Project Tests | `01_run_tests.py --project-only --verbose` | `core`, `tests` | configurable tolerance |
| **4** Project Analysis | `02_run_analysis.py` | `core` | hard fail |
| **5** Connector Search | `08_connector_search.py` | `science` | skipped if not configured |
| **6** Provenance Record | `09_provenance_record.py --stage Connector Search` | `provenance` | skipped if not configured |
| **7** PDF Rendering | `03_render_pdf.py` | `core` | hard fail |
| **8** Output Validation | `04_validate_output.py` | `core` | warning + report |
| **9** LLM Scientific Review | `06_llm_review.py --reviews-only` | `llm` | skipped if Ollama absent |
| **10** LLM Translations | `06_llm_review.py --translations-only` | `llm` | skipped if Ollama absent |
| **11** Copy Outputs | `05_copy_outputs.py` | `core` | soft fail |
| **12** Ebook Generation | `11_ebook_generation.py` | `core`, `ebook` | soft fail |
| **13** Metadata Package | `12_metadata_package.py` | `core`, `metadata` | soft fail |
| **14** Executable Bundle | `08_executable_bundle.py` | `bundle` | soft fail |
| **15** Archival Publication | `09_archive_publication.py` | `archival` | soft fail |
<!-- END:STAGE_TABLE -->
