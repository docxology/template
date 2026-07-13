# `.agents/skills/`

Vendored Agent Skills from
[muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering),
pinned by [`../context-engineering.lock.json`](../context-engineering.lock.json).

## Safety and maintenance

- Load `SKILL.md` progressively when its trigger matches; do not preload every
  body into the context window.
- Treat `scripts/` and shell/Python snippets as examples. Never auto-execute
  them; several accept caller-controlled paths or demonstrate credentialed
  shell commands.
- Preserve relative paths when updating a skill.
- Refresh through the audited installer at a pinned commit, reapply and record
  local overlays, then update both upstream and vendored hashes.
- Run the upstream validators plus this repository's skill, runtime-sync, MCP,
  Ruff, mypy, and test gates before changing the pin.
