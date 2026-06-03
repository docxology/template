# AGENTS — docs/

Human-facing documentation for `template_newspaper`. Keep it accurate and
current: when engine behavior or the content schema changes, update the relevant
doc in the same change.

- `syntax_guide.md` is the contract for `content/` — update it whenever the
  loaders in `src/newspaper/content.py` or `config.py` change.
- `architecture.md` explains the drawn-furniture / flowed-body design.
- `agent_instructions.md` is the short rulebook for agents (mirrors top-level AGENTS.md).
- Images (`front-page.png`, `contact-sheet.png`) are regenerated with `pdftoppm`
  from the current PDF — refresh them when the look changes materially.
