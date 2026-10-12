# setup-acceptance-model

Prepares one pinned local model and its owned daemon on the isolated GitHub-hosted acceptance runner.
Call after checkout and Python setup. Fixed release archives are admitted by
exact byte length and SHA-256 before extraction or execution. Preparation
failures block the observation; they cannot certify an acceptance gate.

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
