# Locked offline native dependency cache

Call this composite after checkout and the existing Python/uv setup. It warms
the Source-locked build and native execution requirements using the existing
hash-required export and installation commands in a fresh job-owned cache.
The calling job receives `UV_CACHE_DIR` through `GITHUB_ENV`.

Functional installed-contract jobs and [native readiness preparation](../setup-native-installed-readiness/README.md)
share these commands. Preparation precedes execution-account handoff and the
original observation deadline. A restored environment or ordinary `uv sync`
alone does not establish the hash-required offline cache prerequisite.

Root and project locks remain unchanged. The subsequent cold factory still
exports, builds and installs independently, offline with required hashes;
cache preparation supplies no acceptance evidence. See [AGENTS.md](AGENTS.md).
