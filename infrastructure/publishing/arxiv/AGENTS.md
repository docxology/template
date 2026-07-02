# `infrastructure/publishing/arxiv/`

Local arXiv submission tarball preparation (no network API).

## Public API

```python
from infrastructure.publishing.arxiv import prepare_arxiv_submission
```

### `prepare_arxiv_submission`

```python
prepare_arxiv_submission(output_dir: Path, metadata: PublicationMetadata) -> Path
```

Copies `.tex`, `.bib`, `.cls`, `.bst`, and `figures/` from `output_dir/../manuscript/`, every rendered `.tex` found under `output_dir` (LaTeX produced at render time), the optional `.bbl` from `output_dir/pdf/`, and writes `arxiv_submission_YYYYMMDD.tar.gz` under `output_dir`.

> ⚠️ **Partial-package honesty.** arXiv requires LaTeX source, not a PDF. Template manuscripts are authored in Markdown and compiled straight to PDF, so `manuscript/` usually contains no `.tex` and the render step does not persist one under `output/` by default. When no `.tex` is present in either location, the tarball is a **references/figures-only partial package** (typically just `references.bib`) that requires manually adding the compiled `.tex` before arXiv will accept it. The test `TestPrepareArxivSubmission::test_markdown_only_manuscript_is_references_only` binds this contract; `test_rendered_tex_from_output_included` binds the rendered-`.tex` inclusion path.

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_platforms.py::TestPrepareArxivSubmission -v
```

## See also

- [`README.md`](README.md)
- [`../platforms.py`](../platforms.py) — backwards-compatible re-export
