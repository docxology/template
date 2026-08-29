# Monid agent skill

Upstream agent skill for the [Monid CLI](https://monid.ai) — discover, inspect,
and run hundreds of data endpoints.

| File | Purpose |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Upstream skill (sync from https://monid.ai/SKILL.md) |
| [`AGENTS.md`](AGENTS.md) | Folder contract |

Python API: [`infrastructure/search/monid/`](../../infrastructure/search/monid/).

Refresh:

```bash
curl -fsSL "https://monid.ai/SKILL.md" -o .agents/skills/monid/SKILL.md
```
