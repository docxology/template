# arXiv submission package

Build a deterministic, non-partial `.tar.gz` LaTeX source candidate for manual
arXiv upload from a project's manuscript and rendered outputs.

```python
from infrastructure.publishing.arxiv import prepare_arxiv_submission

tar_path = prepare_arxiv_submission(Path("projects/my_project/output"), metadata)
```

## Package contract

The renderer-owned `output/pdf/_combined_manuscript.tex` is the preferred main
file. The package places it at the archive root, includes the matching
`_combined_manuscript.bbl` (arXiv requires the `.tex` and `.bbl` stems to
match), rendered `.bib` dependencies, and arXiv-supported image files from
`output/figures/`. Renderer-relative
`../figures/` paths in `\includegraphics` commands are adjusted to the flat
archive layout. A sole noncanonical `output/pdf/*.tex` is supported for older
renderers; multiple candidates fail as ambiguous. If no rendered source exists,
a conventional sibling `manuscript/` TeX tree is preserved by relative path.

The build fails closed when it cannot find a nonempty TeX root. It never emits a
references-only archive. Symlinks and special files are rejected, hidden files
are omitted, unrelated render intermediates are excluded, and colliding target
paths must be byte-identical. The staging directory and every older
`arxiv_submission_*.tar.gz` are removed before each attempt, including a failed
attempt, so a stale archive cannot look current.

`SOURCE_DATE_EPOCH` controls the UTC date in
`arxiv_submission_YYYYMMDD.tar.gz` and all tar/gzip timestamps. A present but
invalid or negative value fails. With no explicit value, deterministic mode
uses the repository `HEAD` epoch. Archive members have lexical ordering and
normalized ownership/modes, so identical inputs plus the same epoch produce
identical bytes.

## Public tracked package workflow

Prepare the arXiv package only after the final canonical render. Packaging adds
stable files under `output/`, so a tracked public exemplar must then refresh its
integrity snapshot and rerun Stage 4; Stage 4 writes the validation report and
the corresponding rendered-provenance receipt for the updated output tree.

```bash
export SOURCE_DATE_EPOCH="$(git log -1 --format=%ct)"
uv run python - <<'PY'
from pathlib import Path

from infrastructure.publishing import prepare_arxiv_submission
from infrastructure.publishing.metadata_from_config import publication_metadata_from_config

project = Path("projects/templates/template_active_inference")
metadata = publication_metadata_from_config(project / "manuscript/config.yaml")
print(prepare_arxiv_submission(project / "output", metadata))
PY
uv run python scripts/maintenance/refresh_artifact_manifests.py \
  --project templates/template_active_inference
uv run python scripts/pipeline/stage_04_validate.py \
  --project templates/template_active_inference
```

Do not follow this with `refresh_rendered_provenance.py`: that maintenance
helper intentionally rerenders first, and the render clean step removes the
post-render package. Run the arXiv workflow again after any later render. Before
upload, inspect the tar members and verify arXiv's generated PDF in its manual
submission preview; local packaging does not prove remote TeX compatibility and
is not publication or upload authority. See arXiv's current
[TeX submission guidance](https://info.arxiv.org/help/submit_tex.html) before
uploading.

See [AGENTS.md](AGENTS.md).
