# setup-native-loader-fixture

Warms the Source-locked dependency cache used by the genuine offline installed
native-loader test. Call after checkout and Root Python environment setup:

```yaml
- uses: ./.github/actions/setup-native-loader-fixture
```

The action has no inputs or outputs. It requires `uv`, an existing
`$GITHUB_WORKSPACE/.venv/bin/python`, and disposable `$RUNNER_TEMP` storage.
Network access is enabled only for preparation; this action does not run or
certify the offline native-loader test.

The runtime requirement export comes from Root's locked rendering group and is
filtered for the actual interpreter minor by `locked_dependency_export`. A fresh
scratch virtual environment first receives the hash-verified `installed-build`
group. The runtime requirements are then acquired with hash verification,
without dependency resolution or build isolation, so source builds use those
prepared build tools rather than an unrelated environment.

The scratch directory is removed on exit. Acquired dependencies remain in the
normal `uv` cache for the later offline invocation. No Source lock, runtime
deadline, acceptance receipt, or installed-test assertion is changed by this
preparation. See [AGENTS.md](AGENTS.md) for the maintenance contract.
