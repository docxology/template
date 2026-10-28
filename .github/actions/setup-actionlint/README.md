# setup-actionlint

Composite action: pinned, checksum-verified `actionlint` provisioning and run.

```yaml
- uses: ./.github/actions/setup-actionlint
```

The workflow YAML syntax gate (`GH-ACTIONLINT-1`) needs no Python environment and
no project dependencies, so both callers run it as a standalone job in the first
wave:

| Caller | Job |
| --- | --- |
| [`ci.yml`](../../workflows/ci.yml) | `actionlint` — required by `CI Gate` |
| [`hardening.yml`](../../workflows/hardening.yml) | `actionlint` — required by `Hardening Gate` |

The single pin lives in [`action.yml`](action.yml): the `rhysd/actionlint` release
commit (`ACTIONLINT_REF`), the rendered version (`ACTIONLINT_VERSION`), and the
SHA-256 of the release's `scripts/download-actionlint.bash`
(`ACTIONLINT_SCRIPT_SHA256`). The installer is fetched from the immutable commit,
verified with `sha256sum --check --status`, and only then executed. The runner's
preinstalled `shellcheck` is picked up by `actionlint`, so embedded `run:` scripts
are linted too.

## Editing

- Bump all three constants together; a version bump without the script digest
  fails the job by design.
- The gate must stay read-only: no `uv sync`, no checkout of anything but the
  repository itself.
- Run the action and keep the sibling README/AGENTS pair current.
