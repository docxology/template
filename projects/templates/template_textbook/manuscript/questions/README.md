# Question Banks

Self-check questions, one bank per chapter, graded by cognitive demand from
recall through application to synthesis.

## Convention

- **One bank per chapter.** A chapter with stem `<stem>` in part `<part>` has a
  bank at `questions/<part>/q_<stem>.md`.
- **Label:** the H1 carries `{#sec:q_<part>_<stem>}`, e.g.
  `# Question Bank — ... {#sec:q_part_0_orientation}`.
- **Backlink:** the first line links the parent chapter with
  `[@sec:<part>_<stem>]`.
- **Display title** is derived from the parent chapter title by
  [`src/textbook/toc.py`](../../src/textbook/toc.py); list only the file name in
  `config.yaml`.

## Structure of a bank

Three graded sections, numbered continuously:

1. **Recall** — definitions and direct facts from the chapter.
2. **Application** — apply a concept or a `textbook.models` formula to a case.
3. **Synthesis** — connect ideas across sections or chapters.

Each question carries a parenthetical answer, e.g.
`*(Answer: <!-- STUB -->)*`. Fill the `<!-- STUB -->` markers; keep the grading
structure.

## Adding or editing a bank

1. ensure the bank is listed under `appendices.questions` for its part in
   [`../config.yaml`](../config.yaml);
2. run `uv run python scripts/scaffold_chapter.py` to materialise any missing file;
3. write questions and answers, escalating recall → application → synthesis;
4. run `uv run python scripts/audit_textbook_quality.py` and
   `uv run --extra dev python -m pytest`.

See [`AGENTS.md`](AGENTS.md) for the machine-readable contract.
