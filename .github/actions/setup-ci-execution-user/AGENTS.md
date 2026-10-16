# Execution-account contract

This is a thin Linux-only setup action. Business logic and validation belong in
`infrastructure/core/testing/ci_execution_user.py`, with genuine controls in
`tests/infra_tests/core/test_ci_execution_user.py`.

Prepare only after the caller's complete inputs and before custody. Require a
fresh unprivileged account, coherent credentials, unchanged global process
visibility, exact Git/source bytes and modes, and independent cache inodes before
ownership changes. Never substitute an unreadable process for verified absence.

Keep environment forwarding explicit and free of tokens or authentication
configuration. Preserve original command arguments and exit status. Export only
the byte-identical readiness evidence into the declared transport directory;
keep original evidence permissions unchanged. Services started during preparation
retain their existing ownership and identity-checked cleanup.
Prune only Source-declared disposable pytest scratch; retain the bounded exclusion
record and refuse unexpected links or special files in the remaining evidence.

Changes require actionlint, the focused genuine helper controls, independent
review, and affected hosted Linux execution. Local static checks do not qualify
user creation, credential transitions or the release producer.
