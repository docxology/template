# Branch protection checklist

> **Administrator action required.** This checklist documents the required
> GitHub repository settings for the `main` branch. Repository files alone
> cannot prove these settings are active — a repository administrator must
> verify them in GitHub Settings.

## Required status checks

The following CI jobs must be configured as required status checks on `main`
via **Settings → Branches → main → Require status checks to pass before
merging**:

| # | Job display name (from `ci.yml` `name:`) | Job id | Conditional? |
| --- | --- | --- | --- |
| 1 | Lint & Type Check | `lint` | No — always runs |
| 2 | Static Health Report | `health` | No — always runs |
| 3 | Verify No Mocks Policy | `verify-no-mocks` | No — always runs |
| 4 | Infra Tests (ubuntu-latest, Python 3.10) | `test-infra` | No — matrix cell |
| 5 | Infra Tests (ubuntu-latest, Python 3.11) | `test-infra` | No — matrix cell |
| 6 | Infra Tests (ubuntu-latest, Python 3.12) | `test-infra` | No — matrix cell |
| 7 | Infra Tests (ubuntu-latest, Python 3.13) | `test-infra` | No — matrix cell |
| 8 | Infra Tests (macos-latest, Python 3.12) | `test-infra` | No — matrix cell |
| 9 | Regression Tier (claim-binding pins) | `test-regression` | No — always runs |
| 10 | Project Tests (per exemplar × py3.10/py3.12) | `test-project` | No — matrix expands from `detect-projects` |
| 11 | Validate Manuscripts | `validate` | No — always runs |
| 12 | Security Scan | `security` | No — always runs |
| 13 | Documentation Lint | `docs-lint` | No — always runs |
| 14 | Performance Check | `performance` | No — always runs |

**Conditional jobs — must NOT be required:**

| Job display name | Job id | Why not required |
| --- | --- | --- |
| Setup hook (Windows smoke) | `setup-hook-windows-smoke` | Skipped (not failed) when no project ships `setup_hook.py` |
| fep_lean (gauss + lake) | `fep-lean` | Skipped when `projects/fep_lean/lean/lean-toolchain` is absent |

Requiring a skipped job would wedge every PR — GitHub cannot pass a required
check that never runs.

## Required review

- **Require pull request reviews before merging:** at least **1** approving
  review.
- **Require review from Code Owners:** enable "Require review from Code
  Owners" so that changes to sensitive paths (listed in
  [`CODEOWNERS`](../../.github/CODEOWNERS)) automatically request review from
  the designated owner.

## Sensitive-area ownership

The authoritative sensitive-area map is
[`sensitive-ownership.yaml`](../../.github/sensitive-ownership.yaml). Every
sensitive area currently has a sole-owner exception because a second
maintainer is not available. The exception requires:

1. **Green blocking CI** — every required status check above must pass.
2. **Recorded independent adversarial review** — a review by someone other
   than the sole owner must be recorded on the PR, or an explicit
   risk-acceptance must be documented.

The sensitive areas are:

- `infrastructure/steganography/`
- `infrastructure/publishing/`
- `scripts/publish/`
- `.github/workflows/`
- `rules/templates/*/strong/`
- `infrastructure/core/credentials.py`
- `infrastructure/project/git_guards.py`
- `scripts/audit/check_tracked_all.py`
- `infrastructure/rendering/`
- `infrastructure/llm/`
- `infrastructure/search/`
- `infrastructure/provenance/`

## Additional settings

- **Allow auto-merge:** enable in Settings → General → "Allow auto-merge" so
  the [`dependabot-automerge.yml`](../../.github/workflows/dependabot-automerge.yml)
  workflow can auto-merge safe (minor/patch) Dependabot PRs.
- **Do not allow force pushes** to `main`.
- **Do not allow deletions** of `main`.

## Verification

After configuring branch protection, verify by:

1. Opening a test PR that touches a sensitive path.
2. Confirming that the required checks run and block merging.
3. Confirming that Code Owners are automatically requested.
4. Confirming that a PR with failing checks cannot be merged.

## See also

- [`ownership-and-promotion.md`](ownership-and-promotion.md) — sensitive
  ownership exceptions and private-project promotion attestation
- [`threat-model.md`](threat-model.md) — repository-wide threat model
- [`.github/AGENTS.md`](../../.github/AGENTS.md) — CI job details and local
  parity commands
