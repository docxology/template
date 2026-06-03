# AGENTS — content/

This directory is the **single source of truth for the edition**. To change the
paper, edit here — never `src/`.

- `edition.yaml` drives the masthead, render settings, and the ordered page list.
- Each `pages/*.yaml` is one page; the schema is in `../docs/syntax_guide.md`.
- Keep content fictional/illustrative (template edition).
- After editing, re-render and **look** at the affected page; watch the render
  report for over-set (dropped copy). Compact boxes don't fill tall columns —
  prose does.
