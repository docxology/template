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

## Conventions

- Pin third-party actions to a full commit SHA with a trailing `# vX.Y.Z`
  comment, matching `ci.yml`. Bump the SHA here once, not per calling job.
- Keep each action single-purpose; callers compose them with their own
  job-specific steps (`uv sync --group …`, pandoc, TeX Live, …).
- `actionlint` validates these as part of the CI `actionlint` job.
