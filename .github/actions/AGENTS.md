# `.github/actions/` — technical reference

Repository-local composite actions for the CI pipeline. See
[`README.md`](README.md) for the purpose and conventions.

## Contract

- Each subdirectory is one composite action defined by an `action.yml`
  (`runs.using: composite`).
- Referenced from workflows as `uses: ./.github/actions/<name>`. The caller
  **must** run `actions/checkout` before the reference resolves; a local action
  is read from the checked-out workspace, not fetched.
- Third-party `uses:` inside an action are SHA-pinned with a `# vX.Y.Z` comment,
  identical to the policy in [`../workflows/ci.yml`](../workflows/ci.yml).

## Files

| Path | Role |
| --- | --- |
| [`setup-python-env/action.yml`](setup-python-env/action.yml) | uv + Python provisioning (see its [`AGENTS.md`](setup-python-env/AGENTS.md)). |
| [`setup-docs-lint/action.yml`](setup-docs-lint/action.yml) | Shared Node + Mermaid + Chrome provisioning for both blocking documentation-lint callers. |

## Editing

- Bump a shared action SHA here once; every calling job inherits it.
- After any change, run `actionlint` (CI parity: the `actionlint` job).
- Adding a new action directory requires its own `README.md` + `AGENTS.md`
  (the doc-pair invariant — `infrastructure/validation/docs/doc_pair_lint.py`).

The complete hosted acceptance workflow also uses
[`setup-acceptance-documents`](setup-acceptance-documents/README.md) and
[`setup-acceptance-model`](setup-acceptance-model/README.md) to prepare its
source-declared tools and one owned pinned local model before observations.

[`setup-acceptance-fixtures`](setup-acceptance-fixtures/README.md) materializes
identical pinned source inputs for all complete acceptance and release readers.
