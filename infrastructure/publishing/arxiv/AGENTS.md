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

Copies `.tex`, `.bib`, `.cls`, `.bst`, and `figures/` from `output_dir/../manuscript/`, optional `.bbl` from `output_dir/pdf/`, and writes `arxiv_submission_YYYYMMDD.tar.gz` under `output_dir`.

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_platforms.py::TestPrepareArxivSubmission -v
```

## See also

- [`README.md`](README.md)
- [`../platforms.py`](../platforms.py) — backwards-compatible re-export
