# Pipeline diagram

[`pipeline-evidence.dot`](pipeline-evidence.dot) is the editable Graphviz
source for `pipeline-evidence.png`. The diagram traces the input, rendering,
and validation stages described in the [manuscript](../README.md).

Regenerate the image from this directory after editing the diagram.

```bash
dot -Tpng pipeline-evidence.dot -o pipeline-evidence.png
```

[The figure registry](figure_registry.json) records the project-owned label,
caption and accessibility text. The build stages it alongside the image.
