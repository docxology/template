# Style guide — `traditional_newspaper`

## Local habits

- **Thin scripts:** No numerical or layout algorithms in `scripts/`; call `newspaper.*` only.
- **Explicit paths:** Documentation and comments should name real files (`sections.py`, `01_front_page.md`) instead of “the config” or “the main file”.
- **Understated prose:** Prefer short factual sentences in README-style docs; avoid marketing adjectives.

## Repository standards

This project follows the template’s shared rules:

- Testing and no-mock policy: root `.cursorrules/` and [testing_philosophy.md](testing_philosophy.md).
- Type hints and logging: match patterns in existing `src/newspaper/*.py` (see [../src/newspaper/AGENTS.md](../src/newspaper/AGENTS.md)).

## See also

- [agent_instructions.md](agent_instructions.md) — hard constraints for agents
- [../../AGENTS.md](../../AGENTS.md) — `projects/` paradigm overview
