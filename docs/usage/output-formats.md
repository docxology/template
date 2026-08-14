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
| **PDF** | on | `output/<qualified-project>/pdf/<name>_combined.pdf` | `application/pdf` | xelatex via pandoc |
| **HTML** | on | `output/<qualified-project>/web/index.html` | `text/html` | pandoc |
| **Slides** | on | `output/<qualified-project>/slides/<section>_slides.pdf` | `application/pdf` (beamer) | xelatex via pandoc |
| **DOCX** | opt-in | `output/<qualified-project>/docx/<name>_combined.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | pandoc |
| **EPUB** | opt-in | `output/<qualified-project>/epub/<name>_combined.epub` | `application/epub+zip` | pandoc |

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

### Via environment variables

```bash
ENABLE_DOCX=1 ENABLE_EPUB=1 \
  ./run.sh pipeline --project templates/template_code_project --core-only
```

| Env var | Type | Default | Effect |
| --- | --- | --- | --- |
| `ENABLE_PDF` | `0/1`, `true/false`, `yes/no` (case-insensitive) | `1` | Combined PDF + per-section LaTeX/PDF |
| `ENABLE_HTML` | same | `1` | Combined HTML index + per-section HTML |
| `ENABLE_SLIDES` | same | `1` | Per-section Beamer PDFs |
| `ENABLE_DOCX` | same | `0` | Combined Microsoft Word document |
| `ENABLE_EPUB` | same | `0` | Combined EPUB e-reader bundle |

The intended and public precedence contract is an explicitly set
`ENABLE_<FORMAT>` environment variable over `render.formats.<format>` in YAML,
then the dataclass default. Direct users of the Python API may instead pass a
fully constructed `RenderingConfig`.

**Known implementation defect:** `RenderingConfig.from_project_config()`
currently applies YAML after reading the environment, so YAML wins when both
sources set the same format. Until that implementation and its mixed-source
tests are corrected, set a given format in only one source. Environment-only
and YAML-only configurations behave as documented.

## What each format produces

### PDF (`output/<qualified-project>/pdf/`)

- `<project>_combined.pdf` — the single canonical deliverable. Driven by the
  pandoc + xelatex pipeline; includes title page, TOC, bibliography, and all
  manuscript sections in order.
- Auxiliary LaTeX artefacts (`.aux`, `.bbl`, `.tex`, `.log`) support debugging
  and provenance inspection. Let the cleanup stage manage them; do not assume
  every tracked or release-bound artifact is disposable.

### HTML (`output/<qualified-project>/web/`)

- `index.html` — the combined HTML manuscript.
- One `<section>.html` per manuscript section, useful when previewing a
  single section in isolation.
- Figures and cross-references are processed with `pandoc-crossref` when it is
  installed; the renderer logs a warning when the filter is unavailable.

### Slides (`output/<qualified-project>/slides/`)

- One Beamer PDF per manuscript section (`<section>_slides.pdf`). Generated
  from the same source markdown via the `slides_renderer.py` module.
- Use the `render:skip-beamer` HTML comment in a section to suppress its
  slide deck.

### DOCX (`output/<qualified-project>/docx/`)

- `<project>_combined.docx` — the full manuscript as a Microsoft Word
  document, suitable for journal submission, collaborative editing, or
  reviewer markup.
- Citations are processed with Pandoc `--citeproc`, subject to the
  multi-bibliography boundary below.
- An optional reference-doc template can be supplied to the renderer call —
  see `infrastructure/rendering/docx_renderer.py`.

### EPUB (`output/<qualified-project>/epub/`)

- `<project>_combined.epub` — the manuscript as an e-reader bundle (zip of
  XHTML + manifest + optional cover image).
- Use the `cover_image` kwarg on the renderer call to bundle a cover.

### Multi-bibliography boundary

Single-bibliography projects are unaffected. For a manuscript containing more
than one top-level `.bib` file, the current combined PDF path unions all of
them, combined HTML uses the conventional `references.bib`, and DOCX/EPUB use
only the first filename in sorted order. A multi-bibliography exemplar such as
`templates/template_search_project` can therefore have citation differences
between editions. Keep one consolidated `references.bib` when DOCX/EPUB parity
is required, and verify citations in every enabled format. Full parity should
not be claimed until the renderers share one bibliography resolver and tests
cover multiple `.bib` files.

## Cross-format dependency

DOCX and EPUB reuse the **preprocessed combined markdown** produced by the
PDF rendering stage (`_combined_manuscript.md` under the project working
`output/pdf/`).
If you disable PDF via `render.formats.pdf: false`, the DOCX/EPUB stages
log:

```text
[skip] DOCX rendering: no combined markdown found (combined-PDF stage may have been skipped or failed)
```

To produce DOCX or EPUB, currently leave `render.formats.pdf: true`. If a
distribution must omit PDF, select the desired files during packaging rather
than manually deleting evidence from the working output.

## Verifying outputs

```bash
# All combined artifacts in the project working output
find projects/templates/template_code_project/output -type f \
  -name '*_combined*' -newer pyproject.toml

# Check DOCX MIME
file -b --mime-type projects/templates/template_code_project/output/docx/*.docx

# Verify EPUB structure
unzip -l projects/templates/template_code_project/output/epub/*.epub | head -20
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
