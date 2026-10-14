# Image Management Guide

## Manuscript figures

Generate scientific figures from tested project code and save the files under
that project's `output/figures/`. Declare each figure's `fig:` label, filename,
visible caption, generating function, and concise alt text in a project-owned
specification. Publish the registry from the files emitted by the same run.

Manuscript source uses Pandoc image syntax and bracket-cite cross-references:

```markdown
![Objective value by optimization iteration.](../output/figures/convergence.png){#fig:convergence width=80% fig-alt="Line plot of objective value against iteration."}

[@fig:convergence] summarizes the analysis.
```

The visible caption and alt text serve different reading needs. Inject changing
statistics from analysis output into the caption or nearby prose. A complex
figure also needs a nearby prose or appendix description of its relationships.
See [Manuscript Semantics](../guides/manuscript-semantics.md) and the
[Visualization Guide](visualization-guide.md).

## Generated figure registries

The supported APIs live in `infrastructure.documentation`:

| API | Purpose |
| --- | --- |
| `build_generated_figure_registry(specs, generated_paths, schema_version=...)` | Validate declared specifications and the files produced by the current run. |
| `write_generated_figure_registry(registry_path, specs, generated_paths, schema_version=...)` | Validate and atomically persist registry JSON. |
| `publish_generated_figures(output_dir, specs, generated_paths, schema_version=...)` | Validate the source set, mirror its files, and write the registry. |

Specifications provide `label`, `filename`, `caption`, and `generated_by`;
`alt_text` is recorded under `metadata.alt_text` when provided. Duplicate labels
or filenames, missing files, empty captions, and empty generator names fail
before a registry is published. Keep every manuscript label aligned with its
project-owned specification. The [Visualization Guide](visualization-guide.md)
contains a complete plotting and registry example.

## Figure metadata

`FigureManager` records metadata for interactive or project-owned registration:

```python
from infrastructure.documentation import FigureManager

manager = FigureManager("output/figures/figure_metadata.json")
manager.register_figure(
    filename="convergence.png",
    caption="Objective value by optimization iteration.",
    label="fig:convergence",
    generated_by="project.analysis:generate_convergence",
)
record = manager.get_figure("fig:convergence")
records = manager.get_all_figures()
figure_list = manager.generate_figure_list()
```

The manager retains metadata and registry identifiers. The generated-registry
APIs above validate the actual files for pipeline publication. Figure labels
and manuscript references are authored in Pandoc form; pandoc-crossref assigns
presentation numbers during rendering.

### Title-page covers

Cover artwork is configured separately from the scientific figure registry:

```yaml
paper:  # use `book:` for a book cover
  cover:
    image: "figures/cover.png"
    alt: "Concise description of the cover's meaningful visual content."
metadata:
  language: "en"
  tagged_pdf: true
```

The `alt` value is plain text, not LaTeX. In tagged mode the combined-PDF
renderer preserves TeX-reserved characters as literal PDF alternative text and
fails before replacing an existing PDF when the selected configured cover has
no valid alt string. Tagged metadata is only one PDF/UA prerequisite; inspect
the complete structure tree and reading order before release.

## Validation and troubleshooting

Run manuscript preflight from the repository root:

```bash
uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .
```

If a figure is missing, check that analysis produced the declared file and that
its filename matches the specification. Fix the source or generation step, then
regenerate the registry. A `??` cross-reference calls for checking the matching
`{#fig:label}` identifier and `[@fig:label]` reference.

Image paths in authored manuscript files are relative to `manuscript/`, such as
`../output/figures/convergence.png`. Inspect each figure at final render size for
clipping, labels, fonts, and accessible descriptions.

## See Also

- [General troubleshooting](../operational/troubleshooting/common-errors.md)
- [Figure generation guide](../guides/figures-and-analysis.md)
- [Generated registry source](../../infrastructure/documentation/generated_figure_registry.py)
- [Figure metadata source](../../infrastructure/documentation/figure_manager.py)
