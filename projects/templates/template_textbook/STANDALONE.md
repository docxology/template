# Standalone Fork Guide

## Purpose

`template_textbook` is the modular, fillable book scaffold exemplar: a
book-length manuscript structure, generated chapter/lab/question surfaces,
deterministic figures, Mermaid diagrams, and structural integrity tests.

## Copy This When

Use it for a new technical book where the author wants a scalable scaffold
rather than a finished domain manuscript.

## Clean Copy Command

From the template repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_textbook \
  --dest projects/working/my_textbook \
  --new-name my_textbook
```

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  --exclude '.lake/' --exclude 'lake-packages/' \
  projects/templates/template_textbook/ projects/working/my_textbook/
```

## Required Post-Fork Edits

- Update `manuscript/config.yaml`, `domain_profile.yaml`, `experiment_plan.yaml`,
  `CITATION.cff`, `.zenodo.json`, `codemeta.json`, and `pyproject.toml`.
- Replace title, author, units/chapters, glossary, bibliography, cover assets,
  and chapter prose as the book becomes real.
- Keep `<!-- STUB -->`, `TODO`, and `TKTK` markers visible until domain content
  genuinely replaces them.

## Validation Commands

From the copied project root:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/scaffold_chapter.py
uv run python scripts/generate_figures.py
uv run python scripts/generate_diagrams.py
uv run python scripts/audit_textbook_quality.py
```

For the public exemplar from the template repository root:

```bash
uv run pytest projects/templates/template_textbook/tests/ \
  --cov=projects/templates/template_textbook/src --cov-fail-under=90
```

## Intentional Non-Standalone Dependencies

The project-local scaffold, tests, figures, and diagrams do not require the
template infrastructure layer. The monorepo renderer can add publication polish,
but the fillable scaffold remains intentionally stub-heavy until a fork supplies
domain content.

## What Not To Claim

Do not claim the scaffold is a completed textbook. The stub markers are part of
the honest contract and should remain until replaced by reviewed content.
