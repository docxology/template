# methods_sheaf IMRAD fragments

Sheaf composition Methods section (`08_methods_sheaf.md`). Composed track order is fixed in [`../../../sheaf/manifest.yaml`](../../../sheaf/manifest.yaml).

| Fragment | Role |
| --- | --- |
| [`prose.md`](prose.md) | Pipeline overview; references generated figure and tables |
| [`formalism.md`](formalism.md) | Registry-backed counts (`{{sheaf_track_count}}`, `{{coverage_*}}`); avoid `\mathrm{ord}`-style LaTeX that triggers single-brace hydration lint |
| [`visualization.md`](visualization.md) | Stub; body from `section_figures` renderer and `figures.yaml` numbering |
| [`provenance.md`](provenance.md) | Live validation-spine provenance artifact signpost |
| [`counterexample.md`](counterexample.md) | Live expected-failure matrix signpost |
| [`layers.md`](layers.md) | Stub; body from `layers_report` renderer → registry + matrix tables |

Generated table markers: `<!-- sheaf-layers:registry -->`, `<!-- sheaf-layers:binding-matrix -->`, `<!-- sheaf-layers:legend -->`.
