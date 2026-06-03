# Agent Instructions

Concise rules for AI agents editing `template_newspaper`. (See also the
top-level [`AGENTS.md`](../AGENTS.md).)

## Always

1. **Treat content as data.** Newspaper words/sections change in `content/`,
   never in `src/`. If copy forces a code edit, fix the abstraction.
2. **Verify visually.** After any layout or content change, render and *look*:
   `python scripts/10_generate_figures.py && python scripts/20_render_newspaper.py`
   then `pdftoppm -png -r 100 output/pdf/the-triplicate.pdf /tmp/p` and inspect.
3. **Keep the gates green.** `pytest`, `mypy src/newspaper`, `ruff check`.
4. **Update the docs** when behavior or the content schema changes.

## Never

- Hard-code copy or font names outside `typography.py`.
- Mark a layout claim done from code alone, or treat over-set as a warning.
- Edit anything under `output/` by hand.
- Assume `.ttc` subfont order — verify it.

## Where things live

| Task | File |
|------|------|
| change the paper's content | `content/edition.yaml`, `content/pages/*.yaml` |
| add a layout capability | the right `src/newspaper/` module (see `architecture.md`) |
| add a figure | `src/newspaper/figures.py` + `generate_all` |
| change type/look | `src/newspaper/typography.py` |
| pipeline wiring | `scripts/NN_*.py` |

## Definition of done

12-page PDF renders, `all_pages_fit == True`, pages visually read as a real
newspaper, tests/mypy/ruff green, docs updated.
