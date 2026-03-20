# Rendering Pipeline — Template Meta-Project

## Overview

The template project has a unique rendering pipeline because its manuscript contains `${variable}` tokens that must be resolved before PDF generation. This document traces the full path from Markdown source to final PDF.

## Pipeline Path

```
Stage 02 (Analysis)
├── generate_architecture_viz.py → output/figures/*.png (4 figures)
└── generate_manuscript_metrics.py
    ├── introspection.py → output/data/metrics.json
    └── inject_metrics.py → output/manuscript/*.md (21 rendered chapters)

Stage 03 (Rendering)
├── Discovers output/manuscript/*.md (preference over manuscript/)
├── Pandoc: Markdown → LaTeX (with config.yaml metadata)
├── XeLaTeX: LaTeX → PDF (with biber for bibliography)
└── Output: output/template/pdf/template_combined.pdf
```

## Stage 02: Analysis Scripts

Two scripts execute in alphabetical order:

### 1. `generate_architecture_viz.py`

- Calls `generate_all_architecture_figures(repo_root, project_dir)`
- Produces 4 PNG figures in `output/figures/`
- Figures are referenced by the manuscript chapters

### 2. `generate_manuscript_metrics.py`

- Calls `build_infrastructure_report(repo_root)` to scan the repository
- Constructs a metrics dictionary from the report
- Scans `projects/*/tests/` for per-project test counts
- Writes `output/data/metrics.json`
- Calls `render_all_chapters()` to inject variables into manuscript files
- Writes rendered chapters to `output/manuscript/`

## Stage 03: PDF Rendering

The pipeline's `03_render_pdf.py` contains a render hook (lines 56–62) that detects the presence of `output/manuscript/` and uses it instead of `manuscript/`. This means:

1. The raw manuscript files with `${variable}` tokens stay untouched in `manuscript/`
2. The rendered files with computed values live in `output/manuscript/`
3. Stage 03 picks up the rendered files automatically

### Rendering Process

1. **File discovery**: `manuscript_discovery.py` finds all `*.md` files by numeric prefix
2. **Metadata injection**: `config.yaml` provides title, author, DOI, keywords
3. **Pandoc conversion**: Markdown → LaTeX with bibliography processing
4. **XeLaTeX compilation**: LaTeX → PDF with `biber` for references
5. **Post-processing**: Font embedding, PDF/A checks

### Key Configuration

From `manuscript/config.yaml`:

```yaml
paper:
  title: "\\texttt{template/}: A Modular Approach..."
  subtitle: "Architecture, Ergonomics, and Automated Provenance..."
publication:
  doi: "10.5281/zenodo.template.meta"
  journal: "Journal of Open Research Software"
```

## Output Artifacts

After a successful pipeline run:

```
projects/template/output/
├── data/
│   └── metrics.json                  # Live repository metrics
├── figures/
│   ├── architecture_overview.png     # Figure 1
│   ├── pipeline_stages.png           # Figure 2
│   ├── module_inventory.png          # Figure 3
│   └── comparative_feature_matrix.png # Figure 4
├── manuscript/
│   ├── 01_abstract.md               # Rendered (no ${} tokens)
│   ├── 02_introduction.md
│   ├── 03a_architecture.md
│   ├── ...                          # 21 files total
│   ├── references.bib               # Copied verbatim
│   ├── config.yaml                  # Copied verbatim
│   └── preamble.md                  # Copied verbatim
└── pdf/
    └── template_combined.pdf        # Final rendered PDF

output/template/                      # Copies from Stage 05
└── pdf/
    └── template_combined.pdf
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `${module_count}` appears in PDF | Stage 02 didn't run | Run `generate_manuscript_metrics.py` |
| Missing figure in PDF | Stage 02 figure gen failed | Run `generate_architecture_viz.py` |
| "Division by 0" LaTeX error | Stale `.aux` files | Delete `output/*.aux` and re-run |
| Bibliography not resolved | `biber` cycle incomplete | XeLaTeX runs automatically handle this |
| Wrong test count in PDF | Metrics stale | Re-run Stage 02 to refresh `metrics.json` |
