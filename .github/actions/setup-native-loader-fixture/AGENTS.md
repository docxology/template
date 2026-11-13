# setup-native-loader-fixture contract

This action prepares dependencies, not acceptance evidence. It runs on the
isolated hosted runner after Root's `.venv` exists. Preserve the
Source-controlled lock and the actual interpreter-minor filtering; do not
substitute unconstrained packages or a different Python environment.

The fresh scratch environment must receive the hash-verified `installed-build`
group before runtime acquisition. Non-isolated source builds use that
environment's tools. Keep `--require-hashes`, `--no-deps`, and
`--no-build-isolation` on runtime acquisition; build-tool installation separately
refuses source builds. `UV_OFFLINE=0` is preparation-only, and `UV_FROZEN` is
unset only inside this shell step.

Keep scratch ownership under `RUNNER_TEMP` and its exit cleanup. Do not remove
unrelated caches or environments. The genuine later invocation remains offline
and retains its original process custody, loader checks, and deadlines.
Successful preparation alone does not establish native acceptance.

Maintain this pair with [README.md](README.md). After action changes, exercise
its real hosted preparation and the genuine offline consumer; preserve original
failure diagnostics rather than weakening the consumer or its receipt reader.
