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

Shared manifests live here, and memory is loaded from and saved to
[`state/`](state/README.md). Existing private state outside this directory
remains untouched and excluded from publication.
