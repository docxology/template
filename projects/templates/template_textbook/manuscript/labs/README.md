# Labs

Hands-on activities, one per chapter. Each lab bridges a chapter's concepts to a
concrete, computational exercise using the tested helpers in
[`src/textbook/models.py`](../../src/textbook/models.py).

## Convention

- **One lab per chapter.** A chapter with stem `<stem>` in part `<part>` has a
  lab at `labs/<part>/lab_<stem>.md`.
- **Label:** the H1 carries `{#sec:lab_<part>_<stem>}`, e.g.
  `# Lab — ... {#sec:lab_part_0_orientation}`.
- **Backlink:** every lab links to its parent chapter with
  `[@sec:<part>_<stem>]` in the Background section.
- **Display title** is derived from the parent chapter title by
  [`src/textbook/toc.py`](../../src/textbook/toc.py); list only the file name in
  `config.yaml`.

## Structure of a lab

A scaffolded lab carries: a metadata badge (`<!-- chapter-metadata-badge -->`),
**Objectives**, **Background** (with the chapter backlink), **Procedure**,
**Analysis**, a **Computational Workflow** code block importing from
`textbook.models`, and **Reflection**. Fill the `<!-- STUB -->` markers; keep the
structure.

## Adding or editing a lab

1. ensure the lab is listed under `appendices.labs` for its part in
   [`../config.yaml`](../config.yaml);
2. run `uv run python scripts/scaffold_chapter.py` to materialise any missing file;
3. fill the stubs and wire a real computation into the workflow block;
4. run `uv run python scripts/audit_textbook_quality.py` and
   `uv run --extra dev python -m pytest`.

See [`AGENTS.md`](AGENTS.md) for the machine-readable contract.
