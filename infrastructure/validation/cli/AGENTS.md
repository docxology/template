# infrastructure/validation/cli/ - Validation CLI Documentation

## Purpose

The `infrastructure/validation/cli/` package contains the command-line entry
points for markdown, PDF, repository, and pre-render validation. Run as a
module: `python -m infrastructure.validation.cli <subcommand> ...`.

## Files

- `main.py` — CLI dispatcher (argparse subparsers + handlers)
- `pdf.py` — legacy PDF CLI with `--project` discovery (canonical: `python -m infrastructure.validation.cli pdf …`)
- `__main__.py` — module entry point (delegates to `main.main()`)
- `__init__.py` — package marker

## Subcommands

| Subcommand  | Handler                          | Purpose                                                                |
|-------------|----------------------------------|------------------------------------------------------------------------|
| `pdf`       | `validate_pdf_command`           | Validate a rendered PDF (unresolved refs, missing citations)           |
| `markdown`  | `validate_markdown_command`      | Run all markdown content checks against a manuscript directory         |
| `prerender` | `validate_prerender_command`     | Strict source-markdown gate: pitfalls + undefined citations            |
| `integrity` | `verify_integrity_command`       | Cross-reference and file-integrity check on an output directory        |
| `links`     | `validate_links_command`         | Scan markdown link targets repo-wide and emit a broken-link report     |

### `prerender`

Mirrors the gate that `PDFRenderer.render_combined` runs before Pandoc/xelatex
(`infrastructure/rendering/_pdf_combined_pandoc.py` via the
`_pdf_combined_renderer` facade re-export). Useful as a fast pre-commit /
interactive check that fires in milliseconds and fails the same way the renderer
would, on the same source files.

```bash
# Canonical public exemplar:
# Default discovery: union of manuscript/*.bib next to the markdown (omit --bib)
uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript

# Explicit bibliography path
uv run python -m infrastructure.validation.cli prerender \
  projects/templates/template_code_project/manuscript \
  --bib projects/templates/template_code_project/manuscript/references.bib

# Repo-relative paths in the error output
uv run python -m infrastructure.validation.cli prerender \
  projects/templates/template_code_project/manuscript \
  --repo-root .
```

Exit codes: `0` clean, `1` blockers found (each blocker logged at ERROR with the
file path and a one-line message).

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../../rendering/AGENTS.md`](../../rendering/AGENTS.md) — the gate this CLI surfaces
