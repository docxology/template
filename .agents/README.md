# Repository Agent Skills

The tracked Agent Skills source for cross-runtime use. The current collection
is pinned in [`context-engineering.lock.json`](context-engineering.lock.json),
with upstream attribution and license under [`skills/`](skills/).

```bash
# Read-only parity audit
uv run python -m infrastructure.skills runtime-status

# Reversible user-level install for Codex, Claude Code, and Hermes
uv run python -m infrastructure.skills runtime-install
```

The installer stages an immutable upstream-revision plus local-tree-hash release under
`~/.local/share/template-agent-skills/`, links only the pinned skill names into
each runtime, backs up replaced paths under `~/.local/state/`, and writes a
receipt. It never executes upstream scripts.

Each install keeps an immutable JSON receipt under
`~/.local/state/template-agent-skills/receipts/` and refreshes
`context-engineering.json` as the current-state view.
