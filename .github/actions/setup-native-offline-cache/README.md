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

## Scope selection

Root is always warmed. Complete native roles also install their own locks, so
`project-scopes` names the exact scopes to warm beside Root; it is empty by
default and accepts the space-separated report from
`python -m infrastructure.reporting.native_installed_launcher --print-preparation-scopes`,
which is the same selection the preparation loop uses.

This is required, not optional, whenever a scope resolves a package differently
from Root. In hosted run 41940842593, cell `template_autoresearch_project` (job
126961680266), the action warmed only Root and the cold factory then failed
offline at fixture setup with `Failed to download packaging==26.2`: the Root lock
pins `packaging==26.3`, and the two locks disagree on four packages in total. A
Root-only warm cannot satisfy such a lock, however many times it is restored.
