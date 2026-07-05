# Testing Guide

The book ships with a real test suite, a coverage gate, and a structural audit.
Together they guarantee that the computational backbone is correct *and* that the
manuscript never drifts from its contract — even as you fill thousands of pages.

## Running the suite

All commands use `uv` and assume you are **inside the project directory**
(`projects/templates/template_textbook/`); the `--extra dev` form only resolves
there. From the monorepo root, use the repo-root form instead (`uv run python -m
pytest projects/templates/template_textbook/tests/
--cov=projects/templates/template_textbook/src --cov-fail-under=90`), as shown in
the [`README.md`](../README.md) quick start. The `dev` extra provides `pytest`
and `pytest-cov`.

```bash
# Full suite
uv run --extra dev python -m pytest

# A single file
uv run --extra dev python -m pytest tests/test_manuscript_integrity.py

# A single test
uv run --extra dev python -m pytest tests/test_models.py::test_logistic_growth -v

# With coverage (the gate)
uv run --extra dev python -m pytest --cov=src --cov-report=term-missing
```

`pythonpath = ["src"]`, `testpaths`, and the default options live in
[`pyproject.toml`](../pyproject.toml).

## What is tested

| File | Covers |
| --- | --- |
| [`test_config.py`](../tests/test_config.py) | `load_config`, `iter_chapters`, `validate_config`, `ChapterRef`. |
| [`test_toc.py`](../tests/test_toc.py) | TOC building, chapter numbering, section/lab/question labels. |
| [`test_content.py`](../tests/test_content.py) | `scaffold_chapter`/`scaffold_lab`/`scaffold_question_bank`, `validate_chapter`, stub/word counts. |
| [`test_models.py`](../tests/test_models.py) | The worked formalisms (logistic growth, saturating response, decay, half-life, linear fit, stats, normalization). |
| [`test_visualization.py`](../tests/test_visualization.py) | Deterministic figure generation and the `<part_id>_<stem>.png` filename contract. |
| [`test_mermaid.py`](../tests/test_mermaid.py) | Spec loading, source building, PNG/`.mmd` fallback. |
| [`test_paths_io.py`](../tests/test_paths_io.py) | Path resolution and atomic file I/O helpers. |
| [`test_manuscript_integrity.py`](../tests/test_manuscript_integrity.py) | The manuscript matches the contract (see below). |

## No-mocks policy

There are **no** `MagicMock`, `mocker.patch`, or `unittest.mock` calls anywhere.
Every test uses real data and real computation: real temp files via `tmp_path`,
real numbers fed to `models.py`, real figures written to disk. This is a hard
repository-wide rule — if you add a test, exercise the real function.

## Coverage gate

Project code targets **90% coverage** (`fail_under = 90` in
[`pyproject.toml`](../pyproject.toml), `source = ["src"]`). The current backbone
sits comfortably above the floor. Keep new `src/` code covered: a function with no
test will pull coverage below the floor and fail the gate.

```bash
uv run --extra dev python -m pytest --cov=src --cov-fail-under=90
```

## Manuscript-integrity tests

[`tests/test_manuscript_integrity.py`](../tests/test_manuscript_integrity.py)
turns the authoring contract into executable assertions against the live
manuscript:

- `test_config_is_valid` — `config.yaml` passes `validate_config`.
- `test_all_chapters_exist_and_validate` — every declared chapter file exists and
  satisfies `validate_chapter` (all required headings + tokens present).
- `test_every_chapter_has_lab_and_questions` — each chapter has its matching
  `lab_<stem>.md` and `q_<stem>.md`.
- `test_references_define_every_contract_key` — `references.bib` defines every key
  in `CITATION_KEYS`.
- `test_glossary_defines_every_contract_anchor` — `glossary.md` defines every
  anchor in `GLOSSARY_ANCHORS`.
- `test_chapters_only_cite_defined_keys` — no chapter cites an undefined `[@key]`.
- `test_chapters_only_link_defined_glossary_anchors` — no chapter links an
  undefined `#gl:` anchor.

These run with the rest of the suite, so adding a chapter that breaks the
contract (a missing `Summary`, an undefined citation, a hand-typed figure
number) fails CI immediately.

## The quality / progress gate

[`scripts/audit_textbook_quality.py`](../scripts/audit_textbook_quality.py) is a
structural gate you can run as CI or before publication. It validates the config,
checks every declared chapter exists and passes the contract, confirms each
lab + question file is present, and prints a per-chapter stub-count / word-count
progress table.

```bash
uv run python scripts/audit_textbook_quality.py
uv run python scripts/audit_textbook_quality.py --lenient
```

Strict by default; pass `--lenient` only for partial-tree progress checks. Together with
the integrity tests this is how you grow the book to hundreds of pages and stay
confident the contract is still green — see the
[authoring guide](authoring_guide.md).
