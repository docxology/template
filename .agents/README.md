# Shared agent workspace

Start with [AGENTS.md](AGENTS.md) for generic routing, catalogs and local state.
The repository's [root manual](../AGENTS.md), [onboarding](../START_HERE.md) and
[workflow hub](../docs/prompts/SKILL.md) supply the operating context.

Local descriptors live under [`workflows/`](workflows/); pinned third-party
descriptors stay under [`skills/`](skills/) with their existing lock and license.
Both are available to checkout discovery, the generated index and MCP skill
listing. Root `.agents` files are checkout configuration, rather than assets
automatically installed by the Python wheel.

The optional cross-runtime installer handles only the pinned collection:

```bash
uv run python -m infrastructure.skills runtime-status
# Intentional user-level install, with timestamped backups and a receipt:
uv run python -m infrastructure.skills runtime-install
```

It stages an immutable revision and tree-hash release under
`~/.local/share/template-agent-skills/`, backs up replaced paths under
`~/.local/state/`, and never executes upstream scripts.

Migration from Cursor: the manifests now live here, shared memory writes to
[`state/`](state/README.md), and legacy ignored memory remains readable with a
deprecation warning. Existing private state is preserved. Cursor-specific
adapters can follow [the deprecated bridge](../.cursor/README.md).
