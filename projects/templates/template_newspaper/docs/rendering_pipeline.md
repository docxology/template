# Rendering Pipeline

## The newspaper render (Stage 02)

The newspaper PDF is produced by the project's analysis scripts, which the
repository orchestrator runs in lexicographic order during **Stage 02**:

| Script | Does | Output |
|--------|------|--------|
| `00_preflight.py` | imports deps; loads + validates the edition | exit code |
| `10_generate_figures.py` | builds halftone scenes + charts | `output/figures/*.png` |
| `20_render_newspaper.py` | renders 12 pages; writes reports | `output/pdf/the-triplicate.pdf`, `output/data/render_report.json`, `output/reports/render_summary.txt` |

Internally `20_render_newspaper.py` calls `newspaper.engine.build_and_render`,
which: loads `content/` → registers fonts → opens an invariant ReportLab canvas
at the configured trim → renders each page (`layout.render_page`) → saves the PDF
→ returns a `RenderResult` (`page_count`, `oversets`, `all_pages_fit`).

## The descriptive manuscript (Stage 03)

`manuscript/` holds a short paper *about* the engine. The repository's Stage-03
infrastructure renderer turns it into a standard PDF, exactly as for the sibling
templates. This is independent of the newspaper artifact.

## The full pipeline

```
Clean → Env Setup → Infra Tests → Project Tests → Analysis(02) → PDF Render(03)
      → Output Validation → Copy Outputs
```

`./run.sh --project templates/template_newspaper --pipeline` runs all of it. The
newspaper is produced at the Analysis stage; the descriptive manuscript at the
PDF Render stage.

## Determinism

The canvas is opened with `invariant=True` and figures are drawn from fixed
procedural recipes (no randomness, no timestamps), so identical content yields
identical bytes.
