# Conclusion {#sec:conclusion}

`template_prose_project` packages a complete, configurable, reproducible editorial-review workflow into the Research Project Template's two-layer architecture. By keeping prose analysis, structural validation, and bibliography cross-checking in two orthogonal infrastructure modules — `infrastructure/prose/` and `infrastructure/reference/` — the project demonstrates that *editorial discipline* is just as expressible as a configurable pipeline as *numerical reproducibility* (`template_code_project`) and optional *literature curation* (`projects_archive/template_search_project`).

The permanent exemplars and optional search add-on share a single house style:

* `manuscript/config.yaml` is the only place run policy lives.
* `src/pipeline.py` is the only place the project touches `infrastructure/`.
* Scripts in `scripts/` do only filesystem I/O and CLI argument handling.
* Every artefact in `output/` is regeneratable; `manuscript/references.bib` is the only artefact in the manuscript directory that may be auto-populated (only by the optional search add-on; this project validates but never writes).

The contribution of this exemplar is therefore architectural: a *generic, reusable* prose-quality module that any project in the template can opt into, and a *minimal, configurable* exemplar wiring it to the bibliography and the manuscript pipeline. The combination of `template_code_project` (algorithm + numerical experiments), `template_prose_project` (editorial review), and the optional `projects_archive/template_search_project` add-on (literature discovery + LLM synthesis) covers the dominant shapes of academic research projects in the template; new projects can copy whichever exemplar most closely matches their shape and adjust from there.

Three concrete extensions follow naturally:

1. **Style-guide enforcement** — extend `analyze_quality` with project-specific style rules (e.g. forbidden phrases, required terminology) read from `config.yaml`.
2. **Diff-aware review** — restrict the report to files modified since a given git ref so editorial review can run on every PR.
3. **LLM-assisted rewriting** — pipe long sentences and passive candidates into `infrastructure.llm` for suggested rewrites, using the same `seed=42, temperature=0.0` reproducibility contract as the optional search add-on.
