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

The public precedence contract is an explicitly set
`ENABLE_<FORMAT>` environment variable over `render.formats.<format>` in YAML,
then the dataclass default. Direct users of the Python API may instead pass a
fully constructed `RenderingConfig`.

Precedence is resolved independently for each format, so mixed-source
configuration is supported: an explicit false value remains an override rather
than being treated as absent.

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
- Beamer and Reveal.js decks resolve in-text citations against the shared
  top-level bibliography union. They suppress a repeated bibliography block;
  use the combined manuscript or dedicated references deck for the full list.
- Use the `render:skip-beamer` HTML comment in a section to suppress its
  slide deck.

### DOCX (`output/<qualified-project>/docx/`)

- `<project>_combined.docx` — the full manuscript as a Microsoft Word
  document, suitable for journal submission, collaborative editing, or
  reviewer markup.
- Citations are processed with Pandoc `--citeproc` using the shared
  cross-format bibliography contract below.
- An optional reference-doc template can be supplied to the renderer call —
  see `infrastructure/rendering/docx_renderer.py`.

### EPUB (`output/<qualified-project>/epub/`)

- `<project>_combined.epub` — the manuscript as an e-reader bundle (zip of
  XHTML + manifest + optional cover image).
- Use the `cover_image` kwarg on the renderer call to bundle a cover.

### Cross-format bibliography contract

Single- and multi-bibliography projects use one resolver. Combined PDF and
HTML, Beamer and Reveal.js slides, DOCX, EPUB, and the opt-in ebook stage
discover every top-level `manuscript/*.bib` file, sort by filename, deduplicate
repeated or symlinked paths, and pass the full set to their citation backend
without rewriting manuscript sources. Duplicate citation keys, including
case-only variants within one database or across databases, are an error:
fail-closed handling prevents BibTeX and citeproc from silently selecting
different definitions. The multi-bibliography
`templates/template_search_project` exemplar exercises this contract.

Per-section HTML previews remain intentionally separate: they render a single
section and do not produce a combined bibliography. Slide decks resolve inline
citations from the shared union but intentionally suppress the full references
block in each section deck.

## Cross-format dependency

DOCX and EPUB consume a fresh **shared preprocessed combined Markdown** built
from the current ordered manuscript inputs. PDF-only and slides-only runs also
emit this file when HTML is disabled so every normal render lane has current
composition evidence. The composition is recorded in
`output/reports/manuscript_composition.json`; it does not depend on a PDF
artifact or a prior PDF run. PDF, DOCX, EPUB, and slides toggles can therefore
be selected independently. The receipt-bound combined Markdown remains in the
copied evidence tree even when HTML is disabled; renderer-owned HTML pages and
the favicon do not. Disabled deliverables cannot satisfy current-run
verification.

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
    pdf: false   # skip PDF; other enabled formats remain independent
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

Stages 3–5 use the same effective YAML-plus-environment configuration. Stage 3
removes renderer-owned prior deliverables before producing the enabled formats;
Stage 4 rejects a source output tree that still contains a canonical artifact
for a disabled format; and Stage 5 defensively removes disabled-format artifacts
from the freshly cleaned copied tree before validating each enabled deliverable.
A prior PDF therefore cannot satisfy an HTML-only run or be republished by the
copy stage.

When `slides: true`, at least one current Markdown section must produce a deck;
configuring every section with `<!-- render:skip-beamer -->` is a validation
error rather than a successful zero-deliverable slides run. A project-local
`scripts/_render_pdf_override.py` is the legacy exception to the ordinary
format toggles: all three stages consistently treat that hook as PDF-only.

## See also

- [`../operational/logging/output-design.md`](../operational/logging/output-design.md) — terminal vs file visual contract
- [`../operational/config/configuration.md`](../operational/config/configuration.md) — full env-var + config reference
- [`markdown-template-guide.md`](markdown-template-guide.md) — source-format conventions
- [`../guides/publishing-guide.md`](../guides/publishing-guide.md) — uploading these formats to Zenodo / arXiv / GitHub Releases
- [`../architecture/adrs/003-multi-format-rendering-and-toggles.md`](../architecture/adrs/003-multi-format-rendering-and-toggles.md) — design rationale
