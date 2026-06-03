# `template_newspaper/src/newspaper/` — agent guide

## Purpose

Importable layout engine for the newspaper exemplar. Turns a typed `Edition`
into a print-ready PDF and a machine-readable render report.

## Rules

- Keep the **drawn-furniture / flowed-body** split intact: `furniture.py` draws
  directly on the canvas; `components.py` builds flowables; `layout.py` is the
  only bridge that pours flowables into column frames.
- Keep `geometry.py` free of any rendering-library import — the column
  mathematics must stay trivially testable.
- Keep parsing strict in `content.py` and `config.py`: reject an unknown page
  template or box kind by naming the offending value and the allowed set; never
  silently coerce.
- Never silently drop content — `layout.py` returns and reports over-set pages.
- Keep CLI parsing in `scripts/`; this package exposes callable functions only.
- Preserve determinism: same edition manifest → byte-identical PDF (seed and
  font registration are fixed). Cover new behaviour with tests in `../../tests/`.

## See Also

- [`README.md`](README.md) — module roster and quick reference
- [`../../manuscript/02_engine_architecture.md`](../../manuscript/02_engine_architecture.md) — architecture and method
