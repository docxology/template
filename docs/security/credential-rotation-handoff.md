# Credential Rotation Handoff

Scope: `docxology/template` style public research-project template checkout.
Companion to the threat model ([`threat-model.md`](threat-model.md)) and branch
protection checklist ([`branch-protection-checklist.md`](branch-protection-checklist.md)).

## Purpose

This is the operator runbook for the moment a credential is detected by the
secret scanners. The two scanners cover the staged index and the files tracked
in the current checkout; neither is a full Git-history scanner:

- `scripts/audit/check_tracked_secrets.py` — scan of every file tracked in the
  current checkout (`infrastructure.project.git_guards.tracked_secret_findings`).
- `scripts/audit/check_staged_secrets.py` — pre-commit scan of staged added or
  modified files, reading stage-zero index blobs so partially staged worktree
  edits cannot hide a credential or create a false finding
  (`infrastructure.project.git_guards.staged_diff_secret_findings`).

Both scanners report `path:line:kind` metadata only and never print the matched
value. Kinds are `github-token`, `aws-access-key`, `openai-token`, and
`private-key`. Known low-entropy documentation/test fixtures are ignored so real
credentials are not hidden behind a broad test exclusion.

## Detection

1. **Staged scan (preferred, pre-commit).** Run before every commit, ideally as
   a pre-commit or pre-push hook:

   ```bash
   uv run python scripts/audit/check_staged_secrets.py
   ```

   Exits non-zero on any staged file containing a high-confidence credential
   format. Fix the finding here, before the commit lands.

2. **Tracked-current scan.** Run in CI and pre-push to catch anything in the
   currently tracked tree that slipped past the staged scan:

   ```bash
   uv run python scripts/audit/check_tracked_secrets.py
   ```

   A non-zero exit means the current tracked file contains a credential. A
   clean result does not prove older commits, forks, logs, or release artifacts
   are clean; use an approved history-scanning/incident process when exposure
   may predate the current tree.

## Immediate Containment

When a finding is confirmed (the scanner does not print the value — verify the
matched line by hand before acting):

1. **Stop the leak.** If the credential is staged, unstage and remove it before
   committing:

   ```bash
   git restore --staged <path>
   # edit the file to remove the credential, then re-stage
   ```

2. **Assume compromise.** If the credential was already committed — even once,
   even on a local branch — treat it as leaked. Once a secret enters git
   history it must be rotated, not merely deleted. History rewriting
   (`git filter-repo`, BFG) may remove the blob from this checkout but cannot
   recall clones, forks, mirrors, CI logs, or pull-request diffs that already
   captured it.

3. **Record the finding.** Note the `path:line:kind`, the commit (if any), and
   where the credential was provisioned. This feeds the root-cause review.

## Secret Rotation

Rotate at the issuing provider, not in this repository. Stop affected workflows
and follow the provider's incident procedure. A confirmed compromised secret
should be disabled or revoked as soon as operationally safe; service-continuity
tradeoffs and any brief replacement overlap require an accountable operator,
not an automated assumption.

1. **Identify the issuer.**
   - `github-token` → GitHub personal access token / fine-grained token / app
     installation. Revoke at the token settings page or via `gh`.
   - `aws-access-key` → IAM access key. Deactivate, then delete in the IAM
     console or with `aws iam delete-access-key`.
   - `openai-token` → OpenAI API key. Revoke in the platform dashboard.
   - `private-key` → SSH / TLS / signing private key. Reissue the keypair and
     revoke the public half everywhere it was trusted.

2. **Disable or revoke the exposed credential.** For a confirmed active leak,
   prioritize containment. If continuity policy requires a replacement first,
   keep the overlap bounded, monitored, and explicitly owner-approved.

3. **Provision a replacement if still needed.** Create a new credential with
   the minimum scope needed (least privilege, short expiry, scoped audience).
   Store it in the intended secret store only — see
   [`../reference/`](../reference/) and `infrastructure/core/credentials.py`
   for the runtime credential surface.

4. **Remove the leaked value from this checkout.** If it was staged, drop it
   from the index and the worktree. If it was committed, decide whether history
   rewriting is warranted given the leak already occurred — rotation, not
   history surgery, is the actual mitigation.

## New Credential Deployment

1. Load the new credential only through the supported runtime surface
   (`CredentialManager`, env vars, local `.env` that is git-ignored, or the
   documented local credential JSON). Never paste it into a tracked file.

2. Re-run both scanners to confirm the checkout is clean:

   ```bash
   uv run python scripts/audit/check_staged_secrets.py
   uv run python scripts/audit/check_tracked_secrets.py
   ```

3. If the credential feeds CI, update the GitHub repository secret (or other
   provider secret store) and confirm the next run succeeds against the new
   value. Old secret names should be removed, not left dormant.

## Root-Cause Review

After the credential is rotated and the checkout is clean, record why it
entered the tree in the first place. Update this list as common causes emerge:

- **Pasted into a config or test fixture.** Add a regression test fixture guard
  or move the value behind `CredentialManager` / an env var. Confirm the
  documented-fixture exclusion in `_DOCUMENTED_SECRET_FIXTURE_FRAGMENTS` did
  not mask it.
- **Committed from a private/working project.** Confirm the confidentiality
  guard (`check_tracked_all.py`) covers the path; private trees must stay
  local-only.
- **Generated output leaked a key.** Confirm the public-output secret scanner
  (`tracked_public_output_secrets`) and publication preflight refuse it before
  deposit.
- **Hook was not installed.** Re-install `pre-commit install` and
   `pre-commit install --hook-type pre-push` so the staged scan runs
   automatically.

File follow-up work in [`../../TO-DO.md`](../../TO-DO.md) under the
`SECURITY-*` namespace and link the finding here so the next operator inherits
the context.

## See Also

- [`threat-model.md`](threat-model.md) — TM-003 (credential value leak) and
  TM-011 (generated artifact / oversized output force-add).
- [`branch-protection-checklist.md`](branch-protection-checklist.md) — required
  branch protection so rotation cannot be silently reverted.
- [`ownership-and-promotion.md`](ownership-and-promotion.md) — sensitive-area
  review before private-project promotion.
- `infrastructure/project/git_guards.py` — the scanners themselves.
