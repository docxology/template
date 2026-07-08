# scripts/audit/ — Audit and Quality-Gate Scripts

## Purpose

This subpackage holds **audit and quality-gate orchestrators** for documentation,
file-paths, mock usage, template drift, and tracked-resource hygiene.  None of
these run in the default `./run.sh` pipeline — invoke them directly when needed.

## Scripts

| Script | Delegates to | Purpose |
|--------|--------------|---------|
| `lint_docs.py` | `infrastructure.validation.docs.lint_runner` | Run mermaid + cross-link + consistency linters |
| `check_module_doc_coverage.py` | `infrastructure.validation.docs.module_coverage` | Fail when a package's `AGENTS.md` omits public modules |
| `audit_documentation.py` | `infrastructure.validation.docs` | Advisory RedTeam documentation audit |
| `verify_no_mocks.py` | `infrastructure.validation.mock_checker` | Mock-usage checker across test suite |
| `audit_filepaths.py` | `infrastructure.validation.filepaths` | Repository filepath audit |
| `check_template_drift.py` | `infrastructure.project.drift` | Exemplar doc/code drift check |
| `check_tracked_projects.py` | `infrastructure.project.git_guards` | Confidentiality guard (no private projects committed) |
| `check_tracked_fonds.py` | `infrastructure.project.git_guards` | Fonds resource-pool git guard |
| `check_tracked_rules.py` | `infrastructure.project.git_guards` | Rules resource-pool git guard |
| `check_tracked_tools.py` | `infrastructure.project.git_guards` | Tools resource-pool git guard |
| `check_tracked_all.py` | `infrastructure.project.git_guards` | All-resource git guard (umbrella) |
| `check_tracked_generated_artifacts.py` | `infrastructure.project.git_guards` | Generated-artifact git-index hygiene |
| `copy_exemplar.py` | `infrastructure.project.exemplar` | Copy or update a canonical exemplar |

## Bootstrap pattern

Each script uses `parents[2]` to reach the repo root from `scripts/audit/`:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path
ensure_repo_root_on_path()
```

## Usage

```bash
# Documentation linting
uv run python scripts/audit/lint_docs.py
uv run python scripts/audit/lint_docs.py --mermaid-only

# Template drift
uv run python scripts/audit/check_template_drift.py --strict

# Confidentiality guards
uv run python scripts/audit/check_tracked_projects.py
uv run python scripts/audit/check_tracked_all.py

# Advisory audit
uv run python scripts/audit/audit_documentation.py
```

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`infrastructure/validation/`](../../infrastructure/validation/) — validation infrastructure
- [`infrastructure/project/`](../../infrastructure/project/) — project discovery and guards
