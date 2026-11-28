# Research Project Template infrastructure manuscript

This methods manuscript describes the shared stage runner, how it resolves
manuscript source, and what its output verification records. It is the
root repository's manuscript source. Each exemplar under
[`projects/templates/`](../../projects/templates/) owns its own manuscript.
The earlier infrastructure publication is identified in
[`CITATION.cff`](../../CITATION.cff).

Numbered Markdown files assemble in order. `config.yaml` sets publication
metadata and enabled formats, `preamble.md` supplies PDF typesetting, and
`references.bib` supplies citations. The diagram has an editable Graphviz
source and a checked-in PNG under [assets](assets/README.md).

To regenerate the diagram, run Graphviz from this directory.

```bash
dot -Tpng assets/pipeline-evidence.dot -o assets/pipeline-evidence.png
```

The [standalone manuscript contract](../guides/manuscript-semantics.md#standalone-manuscript-contract)
covers edition settings, covers, numbered equations, and source-bound
render verification.

## Render and validate

Use a clean checkout of this source revision and a separate checkout of
the [pinned template renderer](https://github.com/docxology/template/tree/87704feae0a4490ef7dad9c931d268e8c30273c2).
Install Git, uv, Pandoc, XeLaTeX, and the TeX packages in the
[setup guide](../guides/startup-and-setup.md). The locked runner uses
Python 3.14 by default.

Run from the root of the clean source checkout.

```bash
source_checkout="$(pwd -P)"
project_name="${source_checkout##*/}"
project="working/$project_name"
renderer_checkout="$(mktemp -d)/template"
mkdir -p output/figures
cp docs/manuscript/assets/pipeline-evidence.png docs/manuscript/assets/figure_registry.json output/figures/

git clone https://github.com/docxology/template.git "$renderer_checkout"
git -C "$renderer_checkout" checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
cd "$renderer_checkout"
uv sync --locked
mkdir -p projects/working
ln -s "$source_checkout" "projects/$project"
uv run --no-sync python scripts/pipeline/stage_03_render.py --project "$project"
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project "$project"
```

The registration uses the physical source checkout name so the renderer and
validator agree on the PDF filename. The build resolves `docs/manuscript/`
and writes to `output/` in the source checkout. In a checkout named
`template`, open `output/pdf/template_combined.pdf` and check the ordered
sections, pipeline diagram, and bibliography. Check the verdict in
`output/reports/validation_report.md` and the source bindings in
`output/reports/rendered_provenance.json`.
