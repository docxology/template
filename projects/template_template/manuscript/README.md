# `template/` manuscript (WIP)

Twenty-one numbered Markdown chapters (Abstract through **`08f`**) plus ancillary `preamble.md`, `config.yaml`, `references.bib`. Methods (**`03*`**) split architecture, declarative pipelines, docs policy, FAIR framing, QA. Discussion arcs (**`05*`**) analyse Zero-Mock cost, scalability, comparisons, collaborator guidance, roadmap.

Appendices (**`08a–08f`**) consolidate pipeline YAML mapping, directory sketches, canonical exemplars, documentation inventories, comparative matrices.

## Regenerate placeholders + outputs

From repo root:

```bash
uv run python projects_in_progress/template/scripts/generate_manuscript_metrics.py
```

Promotion note: whilst this tree remains under **`projects_in_progress/template`**, follow `CLAUDE.md`/`resolve_project_root` snippets for `./run.sh` compatibility; canonical exemplars authoritative list → `docs/_generated/active_projects.md`.
