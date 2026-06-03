# AGENTS — Labs

Machine-readable contract for the `labs/` directory. See [`README.md`](README.md)
for prose.

## Invariants

- One lab per chapter. Path: `labs/<part>/lab_<stem>.md` where `<part>` is one of
  `part_0`, `part_I`, `part_II`, `part_III` and `<stem>` matches a chapter stem
  in [`../config.yaml`](../config.yaml).
- H1 label MUST be `{#sec:lab_<part>_<stem>}` and MUST be unique across the book.
- The lab MUST backlink its chapter with `[@sec:<part>_<stem>]`.
- Each lab MUST contain a `<!-- chapter-metadata-badge -->` line and at least one
  `<!-- STUB -->` until fully authored.
- Required sections: **Objectives**, **Background**, **Procedure**, **Analysis**,
  **Computational Workflow** (a fenced ` ```python ` block), **Reflection**.

## Do

- Add lab entries under `appendices.labs` in `config.yaml`, then run
  `scripts/scaffold_chapter.py` to create missing files.
- Use crossref syntax `[@fig:..]`, `[@tbl:..]`, `[@eq:..]`, `[@sec:..]` and
  glossary links `[**term**](../glossary.md#gl:<anchor>)`.
- Import only tested helpers from `textbook.models` in workflow blocks.

## Do NOT

- Hand-number labs or chapters (pandoc-crossref + `toc.py` do this).
- Create a lab file outside the `config.yaml` listing.
- Edit `config.yaml`, `references.bib`, `glossary.md`, or any `.py` engine file
  to satisfy a lab — those are frozen for this template.

## Gates

```bash
uv run python scripts/audit_textbook_quality.py
uv run --extra dev python -m pytest tests/test_manuscript_integrity.py
```
