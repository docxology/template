# run-public-lint

Composite action: the public lint/type gates of the repository, defined once.

```yaml
- uses: ./.github/actions/run-public-lint          # ci.yml
  with:
    safety-scan: "true"                            # join the safety scan wave
- uses: ./.github/actions/run-public-lint          # hardening.yml
  with:
    type-check: ratchet
```

The action resolves the public scopes through
`uv run python -m infrastructure.project.public_scope ci-paths` — the one
source-owned producer of `lint_paths` and `source_paths` — and then runs three
gates concurrently with a separate log each:

| Gate | Command |
| --- | --- |
| Ruff lint | `uv run ruff check "${PUBLIC_CI_LINT_PATHS[@]}"` |
| Ruff format | `uv run ruff format --check "${PUBLIC_CI_LINT_PATHS[@]}"` |
| Types (`mypy`) | `uv run mypy "${PUBLIC_CI_SOURCE_PATHS[@]}"` |
| Types (`ratchet`) | `uv run python scripts/gates/mypy_ratchet.py "${PUBLIC_CI_SOURCE_PATHS[@]}"` |
| Optional safety scan | `bash ../run-safety-scan/scan.sh` |

The scope producer stays sequential: malformed output, an empty scope, or a
rejected CLI call exits before any gate starts. The action then waits for every
child and exits non-zero when any gate failed, printing each gate's log after a
named `PASS`/`FAIL` line, so a failure is never hidden behind a background job.

Every invocation clears `$RUNNER_TEMP/public-lint-logs` first, so a second
invocation inside one job can never print a previous gate's log.

## Editing

- Keep the three commands identical to the documented quality gates; do not add
  `--fix`/in-place formatting here — CI must reject, not rewrite.
- The `safety-scan` input exists so a caller whose job has no other copy of the
  scan can overlap it with the type gate. `run-safety-scan` remains the only
  definition of those commands.
- Run `actionlint` after edits and keep the sibling README/AGENTS pair current.
