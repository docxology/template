# setup-acceptance-model

Prepares one pinned local model and its owned daemon on the isolated GitHub-hosted acceptance runner.
Call after checkout and Python setup. Fixed release archives are admitted by
exact byte length and SHA-256 before extraction or execution. Preparation
failures block the observation; they cannot certify an acceptance gate.

Ollama 0.35.1 runtime acquisition uses the official immutable release-asset API
identities in [`action.yml`](action.yml), with octet-stream content negotiation
and the existing GitHub token scoped only to that preparation step. HTTPS-only
redirects retain curl's ordinary cross-origin authorization stripping; no token
is exported to the daemon or observed case workers. Both OS-specific archive
lengths/hashes and every acquisition/readiness deadline remain authoritative.
Model manifest/blob acquisition remains the separate pinned registry path.

Only the fixed model manifest and blobs are cached in runner-temporary storage.
Every use repeats the pinned length and SHA-256 checks, and rejects symlinks or
mismatched bytes without replacing them. Missing files use the existing bounded
download. The runtime, daemon logs, ownership records and inference evidence stay
in fresh storage. This removes repeated downloads on a valid warm cache; it does
not establish a runtime improvement or make cold acquisition reliable.

See [AGENTS.md](AGENTS.md) for ownership and cleanup requirements.

An owned supervisor remains the process-group anchor throughout observation,
including when the server or its first runner exits. It ignores SIGTERM so
cleanup retains a verified owner until the final whole-group SIGKILL and live
member readback. Cleanup authenticates PID/birth identities and refuses reuse.

The warm-up request explicitly uses `num_ctx=4096` and requires completed actual
inference. It is preparation evidence, not a latency qualification for arbitrary
consumer prompts or output budgets; successful preparation grants no runtime
acceptance and does not change consumer clocks.
