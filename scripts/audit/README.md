# scripts/audit/

Audit and quality-gate scripts for documentation, filepath, drift, and git-guard checks.

## Scripts

| Script | One-liner |
|--------|-----------|
| `lint_docs.py` | Documentation lint (mermaid, cross-links, consistency) |
| `audit_documentation.py` | Advisory RedTeam docs audit |
| `check_backlog.py` | Root/public future-work backlog contract |
| `check_claim_bindings.py` | Complete public claim-binding inventory and source-pin contract |
| `check_public_template_contract.py` | Roster-wide required markers and non-vacuous source/test scope |
| `verify_no_mocks.py` | Lexical mock-framework gate; `--inventory` reports monkeypatch stand-ins |
| `audit_filepaths.py` | Filepath audit |
| `check_template_drift.py` | Template drift check |
| `check_tracked_projects.py` | Confidentiality guard |
| `check_tracked_fonds.py` | Fonds git guard |
| `check_tracked_rules.py` | Rules git guard |
| `check_tracked_tools.py` | Tools git guard |
| `check_tracked_all.py` | All-resource git guard |
| `check_tracked_generated_artifacts.py` | Generated-artifact git-index hygiene |
| `check_tracked_secrets.py` | High-confidence tracked-blob credential scan |
| `check_staged_secrets.py` | High-confidence staged A/C/M/R index-blob scan |
| `copy_exemplar.py` | Copy/update a canonical exemplar |

## Usage

```bash
uv run python scripts/audit/lint_docs.py
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_backlog.py
uv run python scripts/audit/check_claim_bindings.py
uv run python scripts/audit/check_public_template_contract.py --strict
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_secrets.py
uv run python scripts/audit/check_staged_secrets.py
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py --inventory
```

## Notes

- None of these run in the default pipeline — invoke directly.
- Bootstrap uses `parents[2]` from `scripts/audit/` to reach repo root.
- `check_tracked_all.py` is run in pre-push and CI; it applies the project,
  fonds, rules, and tools confidentiality guards together.
- The default no-mocks exit 0 means no prohibited framework imports/calls were
  found. CI additionally runs inventory mode with a zero semantic dependency-
  replacement ceiling; environment isolation is reported but permitted.
