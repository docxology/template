# `template_newspaper/content/pages/` — agent guide

## Purpose

The pages of one edition, as data. One YAML file per page; the layout engine
renders them. No code lives here.

## Rules

- Keep these files pure data — no logic, no code. The engine in
  `src/newspaper/` owns all behaviour.
- Every page file must use a page template and box kinds the loader allows
  (`src/newspaper/content.py`); an unknown value is a hard error, not a warning.
- Keep all stories, names and events illustrative and fictional — this is a
  template edition, not a real paper.
- When adding a page, also register it (in print order) in
  [`../edition.yaml`](../edition.yaml); a page file that is not listed is not
  rendered.
- Follow the schema in [`../../docs/syntax_guide.md`](../../docs/syntax_guide.md);
  do not invent ad-hoc keys.

## See Also

- [`README.md`](README.md) — quick reference and page roster
- [`../AGENTS.md`](../AGENTS.md) — edition-level content contract
