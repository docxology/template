# Linux execution account

Prepare this action after checkout, locked dependencies, tools, services and
downloaded test plans, and before the first source or runtime observation.
Callers must disable checkout credential persistence.

The action delegates setup to
`infrastructure.core.testing.ci_execution_user`. Its fresh unprivileged account
uses the global process namespace and the unchanged strict census. Public input
caches and the job checkout are handed off before custody; shared cache inodes
and hosted tool ownership must remain intact. Prepared model services retain
their original runner ownership and identity-checked cleanup.
Setup executes real zero/nonzero controls through the outer account wrapper and
checks that the payload environment contains none of the named credential keys.

Use the module's `run --state "$RUNNER_TEMP/template-ci-execution/state.json" --`
prefix for each original command. Run its `export` subcommand with the same state
under `always()` before uploading `$TEMPLATE_CI_ARTIFACT_DIRECTORY`. Export copies
the original readiness bytes into a runner-readable transport directory; it does
not change captured source or evidence permissions or establish acceptance.
Source-declared disposable `pytest-tmp` fixtures are excluded from transport;
their bounded exclusion record cannot stand in for receipt evidence.

`docker: "true"` is reserved for a caller that already has the required Docker
access. It does not grant sudo, ptrace capabilities or a relaxed process census.
Linux execution remains a hosted verification obligation.
