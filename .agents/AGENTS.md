# `.agents/`

Public repository-scoped Agent Skills shared across Codex/OpenAI-compatible,
Claude Code, and Hermes runtimes.

## Contract

- [`.agents/skills/`](skills/) is the tracked source used by repository skill
  discovery and by the cross-runtime installer.
- [`context-engineering.lock.json`](context-engineering.lock.json) pins the
  upstream repository, revision, plugin version, inventory counts, and exact
  content digest.
- Upstream skill directories retain their relative references and scripts.
  Scripts are illustrative and must not be auto-executed.
- Runtime-specific policy belongs in an explicit overlay recorded by the lock,
  not in an unrecorded per-runtime copy.

## Verification

```bash
uv run python -m infrastructure.skills runtime-status
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills operations-check
```

Use `... infrastructure.skills runtime-install` only for an intentional user-level install. It
moves same-name existing paths to timestamped backups before linking the pinned
shared store.
