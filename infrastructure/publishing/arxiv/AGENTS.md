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

Prefers the renderer-owned `output/pdf/_combined_manuscript.tex`, stages it at
the archive root with its stem-matched `.bbl`, rendered bibliography files, and
`output/figures/`, and adapts renderer-relative figure references to that flat
layout. If the canonical file is absent, exactly one legacy
`output/pdf/*.tex` is accepted; otherwise a conventional sibling `manuscript/`
TeX source tree is preserved by relative path.

The helper fails closed on a missing/empty or ambiguous TeX root, symlinks,
special files, and non-identical path collisions. It removes all older
date-named packages before building and never leaves a partial package after a
failure. `SOURCE_DATE_EPOCH` controls the UTC filename date and normalized
tar/gzip metadata; invalid or negative explicit values fail. Identical inputs
and epoch must produce byte-identical archives.

Public tracked packages are post-render artifacts: package after the final
Stage 3 render, refresh the current artifact manifest, then rerun Stage 4 so its
validation report and rendered-provenance receipt attest the updated output
tree. Do not run `refresh_rendered_provenance.py` afterward because that helper
rerenders first and cleans the package. The exact command sequence is in
[`README.md`](README.md).

## Tests

```bash
uv run pytest tests/infra_tests/publishing/test_platforms.py::TestPrepareArxivSubmission -v
```

## See also

- [`README.md`](README.md)
- [`../platforms.py`](../platforms.py) — backwards-compatible re-export
