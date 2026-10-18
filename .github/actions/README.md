# `.github/actions/` — local composite actions

Local (repository-scoped) GitHub Actions used to remove duplication from
[`../workflows/ci.yml`](../workflows/ci.yml). They are referenced with a
relative path (`uses: ./.github/actions/<name>`) and therefore require the
repository to be checked out first — a local action's files only exist in the
runner workspace after `actions/checkout` runs.

## Actions

| Action | Purpose |
| --- | --- |
| [`setup-python-env/`](setup-python-env/action.yml) | Provision `uv` (with cache) + Python — the setup block shared by every Python CI job. |
| [`setup-docs-lint/`](setup-docs-lint/action.yml) | Provision Node, Mermaid CLI, and Chrome for every blocking docs-lint caller. |
| [`setup-ci-execution-user/`](setup-ci-execution-user/README.md) | Prepare the unprivileged Linux execution account before strict process observations and export original readiness bytes. |
| [`setup-native-installed-readiness/`](setup-native-installed-readiness/README.md) | Prepare Source-locked native tools and cached inputs before the installed original/reader/handoff operation. |
| [`upload-readiness-shards/`](upload-readiness-shards/README.md) | Check and upload exact bounded native/candidate transport or separately named failed diagnostics. |

## Conventions

- Pin third-party actions to a full commit SHA with a trailing `# vX.Y.Z`
  comment, matching `ci.yml`. Bump the SHA here once, not per calling job.
- Keep each action single-purpose; callers compose them with their own
  job-specific steps (`uv sync --group …`, pandoc, TeX Live, …).
- `actionlint` validates these as part of the CI `actionlint` job.

The complete hosted acceptance workflow also uses
[`setup-acceptance-documents`](setup-acceptance-documents/README.md) and
[`setup-acceptance-model`](setup-acceptance-model/README.md) to prepare its
source-declared tools and one owned pinned local model before observations.

[`setup-acceptance-fixtures`](setup-acceptance-fixtures/README.md) materializes
identical pinned source inputs for all complete acceptance and release readers.

[`setup-native-offline-cache`](setup-native-offline-cache/README.md) shares the
Source-locked hash-required cache preparation between functional installed
contracts and complete native readiness.
