# `tests/regression/projects/template_textbook/` — regression suite

> Pinned regression tests for `template_textbook` structural claims.
> Loads ground truth from
> [`../../pinned_values/template_textbook.json`](../../pinned_values/template_textbook.json).

## Layout

- `tables/` — the manuscript's structural counts (parts, chapters,
  chapters-per-part, labs, question banks). Each value is re-derived
  from the config-driven single source of truth
  (`manuscript/config.yaml`) via the tested `textbook.config` /
  `textbook.toc` loaders and compared to the committed pin.

## Why structural counts

The textbook is a config-driven scaffold: `manuscript/config.yaml`
declares every part, chapter, lab, and question bank, and the loaders
in `textbook.config` / `textbook.toc` turn that config into the table of
contents and numbering. The manuscript prose commits to concrete counts
— "Twelve chapters across four parts" (`front_matter.md`), "(3 chapters)"
per part and "One guided lab / question bank per chapter"
(`manuscript/README.md`). These are exact, deterministic, re-derivable
quantitative claims — ideal stable pins. Adding or removing a part,
chapter, lab, or question in `config.yaml` without updating the prose
drifts a count and fails the test.

See [`../../README.md`](../../README.md) for the philosophy.
