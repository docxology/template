# Branch protection checklist

> **Administrator action required.** This checklist documents the required
> GitHub repository settings for the `main` branch. Repository files alone
> cannot prove these settings are active — a repository administrator must
> verify them in GitHub Settings.

## Required status checks

Required-check configuration is external state. Before changing it, open a
fresh pull request and copy the exact display contexts GitHub reports for the
current workflow; matrix labels and the public project roster can change. The
always-running blocking jobs declared by the current `ci.yml` are:

| # | Job display name (from `ci.yml` `name:`) | Job id | Conditional? |
| --- | --- | --- | --- |
| 1 | Detect optional projects | `detect` | No |
| 2 | Detect public capability matrix | `detect-projects` | No |
| 3 | Actionlint | `actionlint` | No |
| 4 | Lint & Type Check | `lint` | No |
| 5 | Static Health Report | `health` | No |
| 6 | Verify No Mocks Policy | `verify-no-mocks` | No |
| 7 | Infra Tests (`<os>`, Python `<version>`) | `test-infra` | Matrix cells; require the contexts present on the fresh PR |
| 8 | Regression Tier (claim-binding pins) | `test-regression` | No |
| 9 | Project Tests (`<qualified-project>`, `py<version>`) | `test-project` | Matrix derived by `detect-projects`; require the live contexts |
| 10 | Validate Manuscripts | `validate` | No |
| 11 | Security Scan | `security` | No |
| 12 | Documentation Lint | `docs-lint` | No |
| 13 | Performance Check | `performance` | No |

**Conditional jobs — must NOT be required:**

| Job display name | Job id | Why not required |
| --- | --- | --- |
| Setup hook (Windows smoke) | `setup-hook-windows-smoke` | Skipped (not failed) when no project ships `setup_hook.py` |
| fep_lean (gauss + lake) | `fep-lean` | Skipped when the optional local project is absent |
| Public Matrix Receipt | `public-matrix-receipt` | Runs only for scheduled or manually dispatched CI, not pull requests |

Do not require a context that is absent from normal pull-request events. Also
review the list after workflow or matrix changes: a copied static checklist is
not evidence that GitHub's configured rules still match the checkout.

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
5. Comparing GitHub's configured required contexts with the exact contexts on
   that PR, including every current matrix cell and `Actionlint`.

## See also

- [`ownership-and-promotion.md`](ownership-and-promotion.md) — sensitive
  ownership exceptions and private-project promotion attestation
- [`threat-model.md`](threat-model.md) — repository-wide threat model
- [`.github/AGENTS.md`](../../.github/AGENTS.md) — CI job details and local
  parity commands
