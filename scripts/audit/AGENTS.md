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
| `check_backlog.py` | `infrastructure.documentation.backlog` | Root/public future-work and stable-ID contract |
| `check_claim_bindings.py` | `infrastructure.validation.claims` | Complete public claim-binding inventory and source-pin contract |
| `check_public_template_contract.py` | `infrastructure.project.public_template_contract` | Roster-wide public exemplar structure and non-vacuous test-scope gate |
| `verify_no_mocks.py` | `infrastructure.validation.output.no_mock_audit` | Enforced lexical mock-framework gate plus zero-dependency-replacement semantic inventory |
| `audit_filepaths.py` | `infrastructure.validation.filepaths` | Repository filepath audit |
| `check_template_drift.py` | `infrastructure.project.drift` | Exemplar doc/code drift check |
| `check_tracked_projects.py` | `infrastructure.project.git_guards` | Confidentiality guard (no private projects committed) |
| `check_tracked_fonds.py` | `infrastructure.project.git_guards` | Fonds resource-pool git guard |
| `check_tracked_rules.py` | `infrastructure.project.git_guards` | Rules resource-pool git guard |
| `check_tracked_tools.py` | `infrastructure.project.git_guards` | Tools resource-pool git guard |
| `check_tracked_all.py` | `infrastructure.project.git_guards` | All-resource git guard (umbrella) |
| `check_mirror_symlinks.py` | `infrastructure.project.linking` | Mirror-shape guard: every `projects/<lifecycle>/` entry must be a managed symlink; fails on a real dir or unmanaged link dropped into the mirror |
| `check_tracked_generated_artifacts.py` | `infrastructure.project.git_guards` | Generated-artifact git-index hygiene |
| `check_tracked_secrets.py` | `infrastructure.project.git_guards.tracked_secret_findings` | High-confidence credential scan over every tracked blob |
| `check_staged_secrets.py` | `infrastructure.project.git_guards.staged_diff_secret_findings` | Pre-commit credential scan over staged A/C/M/R index blobs |
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

# Path-scoped lint (fast targeted check on slow volumes; full-repo lint can
# exceed several minutes on external drives). Fail-closed on missing or
# repo-escaping paths.
uv run python scripts/audit/lint_docs.py --paths README.md START_HERE.md docs/ --links-only --json

# Template drift
uv run python scripts/audit/check_template_drift.py --strict

# Confidentiality guards
uv run python scripts/audit/check_tracked_projects.py
uv run python scripts/audit/check_tracked_all.py

# Mirror-shape guard (real dirs / unmanaged links under projects/<lifecycle>/)
uv run python scripts/audit/check_mirror_symlinks.py
uv run python scripts/audit/check_tracked_secrets.py
uv run python scripts/audit/check_staged_secrets.py

# Lexical gate and enforced semantic inventory
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py --inventory --max-dependency-replacements 0

# Advisory audit
uv run python scripts/audit/audit_documentation.py
```

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`infrastructure/validation/`](../../infrastructure/validation/) — validation infrastructure
- [`infrastructure/project/`](../../infrastructure/project/) — project discovery and guards
