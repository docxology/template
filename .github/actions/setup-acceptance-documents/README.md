# setup-acceptance-documents

Prepares official document prerequisites on the isolated GitHub-hosted acceptance runner.
Call after checkout and Python setup. Fixed release archives are admitted by
exact byte length and SHA-256 before extraction or execution. Preparation
failures block the observation; they cannot certify an acceptance gate.

See [AGENTS.md](AGENTS.md) for ownership and cleanup requirements.
