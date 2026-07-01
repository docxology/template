# `template_textbook` — structural regression tests

> Re-derives the book's structural counts (parts, chapters,
> chapters-per-part, labs, question banks) from the config-driven single
> source of truth (`manuscript/config.yaml`) via the tested
> `textbook.config` / `textbook.toc` loaders and compares them to the
> pinned ground truth in
> [`../../../pinned_values/template_textbook.json`](../../../pinned_values/template_textbook.json).
