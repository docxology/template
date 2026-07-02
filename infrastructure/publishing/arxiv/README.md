# arXiv submission package

Build a `.tar.gz` of **LaTeX source** for manual arXiv upload from a project's
manuscript directory and build outputs.

```python
from infrastructure.publishing.arxiv import prepare_arxiv_submission

tar_path = prepare_arxiv_submission(Path("projects/my_project/output"), metadata)
```

It collects `.tex`/`.bib`/`.cls`/`.bst` and `figures/` from the sibling
`manuscript/`, any rendered `.tex` found under `output/`, and an optional `.bbl`
under `output/pdf/`.

> ⚠️ **Not upload-ready by default.** arXiv requires LaTeX source, not a PDF.
> Template manuscripts are authored in Markdown and compiled straight to PDF, so
> `manuscript/` usually has no `.tex` and the render step does not persist one.
> When no `.tex` is present, the tarball is a **references/figures-only partial
> package** (typically just `references.bib`) — you must add the compiled `.tex`
> before uploading. Inspect the tarball to confirm a `.tex` is present.

See [AGENTS.md](AGENTS.md).
