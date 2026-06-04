# AGENTS — Question Banks

Machine-readable contract for the `questions/` directory. See
[`README.md`](README.md) for prose.

## Invariants

- One bank per chapter. Path: `questions/<part>/q_<stem>.md` where `<part>` is one
  of `part_0`, `part_I`, `part_II`, `part_III` and `<stem>` matches a chapter
  stem in [`../config.yaml`](../config.yaml).
- H1 label MUST be `{#sec:q_<part>_<stem>}` and MUST be unique across the book.
- The bank MUST backlink its chapter with `[@sec:<part>_<stem>]` in the opening
  line.
- Required graded sections in order: **Recall**, **Application**, **Synthesis**.
- Questions are numbered continuously across the three sections; each carries a
  `*(Answer: ...)*` parenthetical.
- At least one `<!-- STUB -->` remains until the bank is fully authored.

## Do

- Add bank entries under `appendices.questions` in `config.yaml`, then run
  `scripts/scaffold_chapter.py` to create missing files.
- Escalate cognitive demand: recall (fact) → application (use a model) →
  synthesis (connect across sections/chapters).
- Use `[@...]` crossrefs and `[**term**](../glossary.md#gl:<anchor>)` glossary
  links where helpful.

## Do NOT

- Hand-number banks or chapters.
- Create a bank file outside the `config.yaml` listing.
- Edit `config.yaml`, `references.bib`, `glossary.md`, or any `.py` engine file
  to satisfy a bank — those are frozen for this template.

## Gates

```bash
uv run python scripts/audit_textbook_quality.py
uv run --extra dev python -m pytest tests/test_manuscript_integrity.py
```
