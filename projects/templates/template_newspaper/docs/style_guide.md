# Style Guide

## Code

- Python 3.10+, `from __future__ import annotations`, full type hints.
- Pure-logic modules (`geometry`, `content`, `config`) import no rendering
  library, so they stay fast and testable.
- Strict loaders: reject unknown keys / invalid enums with a message that quotes
  the offending value *and* the allowed set.
- Only `typography.py` names a font. Everything else uses `Fonts` roles.
- mypy- and ruff-clean. Keep functions small and single-purpose.
- Docstrings explain *why*, not just *what*; match the surrounding density.

## Typography (the paper's look)

- **Display:** Didot (nameplate, headlines) — high-contrast didone.
- **Text:** Georgia — a screen-and-print serif with a generous x-height.
- **Labels:** Helvetica/Arial — kickers, folios, captions, table heads.
- Headlines never hyphenate (`splitLongWords=0`); body justifies with
  hyphenation on.
- Ink is a near-black gray (newsprint), not pure black; rules are hairlines.
- Hierarchy by size, not by weight alone: lead 44 / primary 23 / secondary 17 /
  minor 12.5 pt.

## Layout conventions

- Tabloid 11×17 default; **4-column** editorial measure (~2.4″ on full-width
  pages, ~1.95″ on the front beside the rail); classifieds run a denser 6-column
  grid; 0.16″ gutters; hairline rules centred in gutters.
- A spanning lead headline is *drawn furniture*; secondary headlines flow at
  single-column width (keep them `secondary`/`minor`).
- Boxes are shaded + ruled; classifieds flow unboxed and dense.
