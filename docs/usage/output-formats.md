# Output formats

> Reference for the five output formats the rendering pipeline emits, the
> `render.formats` config block, the per-format env-var toggles, and the
> on-disk artefact layout.
>
> Companion to [`../operational/logging/output-design.md`](../operational/logging/output-design.md)
> (visual contract for terminal vs file output) and
> [`markdown-template-guide.md`](markdown-template-guide.md) (source-format
> conventions).

## At a glance

| Format | Default | Output path | MIME | Renderer |
| --- | --- | --- | --- | --- |
| **PDF** | on | `output/<project>/pdf/<project>_combined.pdf` | `application/pdf` | xelatex via pandoc |
| **HTML** | on | `output/<project>/web/index.html` | `text/html` | pandoc |
| **Slides** | on | `output/<project>/slides/<section>_slides.pdf` | `application/pdf` (beamer) | xelatex via pandoc |
| **DOCX** | opt-in | `output/<project>/docx/<project>_combined.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | pandoc |
| **EPUB** | opt-in | `output/<project>/epub/<project>_combined.epub` | `application/epub+zip` | pandoc |

Per-format toggles default to PDF/HTML/Slides **on** and DOCX/EPUB **off** —
opt in via `render.formats` in `manuscript/config.yaml`.

## Enabling formats

### Via `manuscript/config.yaml`

```yaml
render:
  formats:
    pdf: true
    html: true
    slides: true
    docx: true     # opt-in
    epub: false    # opt-in
```

The block is validated by the project-config schema in
`infrastructure/core/config/schema.py` — unknown keys under
`render.formats` are rejected at validation time.

### Via environment variables (overrides yaml)

```bash
ENABLE_DOCX=1 ENABLE_EPUB=1 ./run.sh --pipeline
```

| Env var | Type | Default | Effect |
| --- | --- | --- | --- |
| `ENABLE_PDF` | `0/1`, `true/false`, `yes/no` (case-insensitive) | `1` | Combined PDF + per-section LaTeX/PDF |
| `ENABLE_HTML` | same | `1` | Combined HTML index + per-section HTML |
| `ENABLE_SLIDES` | same | `1` | Per-section Beamer PDFs |
| `ENABLE_DOCX` | same | `0` | Combined Microsoft Word document |
| `ENABLE_EPUB` | same | `0` | Combined EPUB e-reader bundle |

Precedence (highest first): explicit `enable_<fmt>=` kwarg → env var →
`render.formats.<fmt>` in yaml → dataclass default.

## What each format produces

### PDF (`output/<project>/pdf/`)

- `<project>_combined.pdf` — the single canonical deliverable. Driven by the
  pandoc + xelatex pipeline; includes title page, TOC, bibliography, and all
  manuscript sections in order.
- Auxiliary LaTeX artefacts (`.aux`, `.bbl`, `.tex`, `.log`) — kept for
  debugging; safe to delete.

### HTML (`output/<project>/web/`)

- `index.html` — the combined HTML manuscript.
- One `<section>.html` per manuscript section, useful when previewing a
  single section in isolation.
- Inline figures, equations, and citations are preserved via pandoc-crossref.

### Slides (`output/<project>/slides/`)

- One Beamer PDF per manuscript section (`<section>_slides.pdf`). Generated
  from the same source markdown via the `slides_renderer.py` module.
- Use the `render:skip-beamer` HTML comment in a section to suppress its
  slide deck.

### DOCX (`output/<project>/docx/`)

- `<project>_combined.docx` — the full manuscript as a Microsoft Word
  document, suitable for journal submission, collaborative editing, or
  reviewer markup.
- Citation processing matches the HTML/PDF pipeline (pandoc `--citeproc`).
- An optional reference-doc template can be supplied to the renderer call —
  see `infrastructure/rendering/docx_renderer.py`.

### EPUB (`output/<project>/epub/`)

- `<project>_combined.epub` — the manuscript as an e-reader bundle (zip of
  XHTML + manifest + optional cover image).
- Use the `cover_image` kwarg on the renderer call to bundle a cover.

## Cross-format dependency

DOCX and EPUB reuse the **preprocessed combined markdown** produced by the
PDF rendering stage (`_combined_manuscript.md` under `output/<project>/pdf/`).
If you disable PDF via `render.formats.pdf: false`, the DOCX/EPUB stages
log:

```text
[skip] DOCX rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)
```

To produce DOCX or EPUB without delivering the PDF artefact, leave
`render.formats.pdf: true` (the PDF is harmless if you ignore it) — or
delete the PDF post-render.

## Verifying outputs

```bash
# All artefacts after a run
find projects/<name>/output -type f -name '*_combined*' -newer pyproject.toml

# Check DOCX MIME
file -b --mime-type projects/<name>/output/docx/*.docx

# Verify EPUB structure
unzip -l projects/<name>/output/epub/*.epub | head -20
```

## Skipping a format

```yaml
render:
  formats:
    pdf: false   # skip combined PDF — DOCX/EPUB will cascade-skip
    html: true
    slides: false
    docx: false
    epub: false
```

Pipeline log shows the skip explicitly:

```text
Render formats: pdf=False html=True slides=False docx=False epub=False
[skip] PDF rendering disabled in config (render.formats.pdf=false)
[skip] Slides rendering disabled in config (render.formats.slides=false)
```

## See also

- [`../operational/logging/output-design.md`](../operational/logging/output-design.md) — terminal vs file visual contract
- [`../operational/config/configuration.md`](../operational/config/configuration.md) — full env-var + config reference
- [`markdown-template-guide.md`](markdown-template-guide.md) — source-format conventions
- [`../guides/publishing-guide.md`](../guides/publishing-guide.md) — uploading these formats to Zenodo / arXiv / GitHub Releases
- [`../architecture/adrs/003-multi-format-rendering-and-toggles.md`](../architecture/adrs/003-multi-format-rendering-and-toggles.md) — design rationale
