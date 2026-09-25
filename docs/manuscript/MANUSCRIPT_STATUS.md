# Manuscript status — template (monorepo infrastructure checkout)

**Repo type:** Layer-1 infrastructure monorepo (generic build/validation
tooling, pipeline orchestration, documentation hub). This checkout is the
`template` infrastructure repository itself, synced from the docxology/template
monorepo; it *hosts* exemplar projects' manuscripts under `projects/templates/`
but is not itself a publication-track research project.

**Evidence checked (2026-08-29):** root `README.md`, `AGENTS.md`, `CLAUDE.md`,
`pyproject.toml` (infrastructure packaging), `docs/` tree (documentation hub
with `README.md`, `AGENTS.md`, `documentation-index.md` and ~30 subdirectories
of guides/reference — no research manuscript), `infrastructure/` module tree.
No `manuscript/` directory exists at repo top level.

**Why no publication-target manuscript applies today:** the repository's
deliverables are tooling and documentation, not research findings. Research
manuscripts belong to the Layer-2 exemplar projects (e.g.
`projects/templates/template_code_project/manuscript/`), each of which
carries the standard manuscript layout.

**What would trigger creating one:** a methods/systems paper *about* the
template architecture itself (cf. the published Zenodo record cited in the
root `README.md`). If pursued, add a standard top-level `manuscript/`
directory per the docxology/template exemplar standard (SECTION files
`00_abstract.md`..`99_references.md`, `config.yaml`, `config.yaml.example`,
`preamble.md`, `references.bib`, `README.md`, `AGENTS.md`), with numeric
claims sourced from `docs/_generated/COUNTS.md` and the measured audit
gates rather than prose estimates.
