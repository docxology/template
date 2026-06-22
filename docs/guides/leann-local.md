# LEANN Local Semantic Retrieval Guide

LEANN is an optional local semantic-retrieval companion for agent-assisted
navigation. It can help find candidate files and concepts when keyword search is
too narrow. It is not a pipeline stage, CI dependency, publication evidence
source, or required developer setup.

Official project: [StarTrail-org/LEANN](https://github.com/StarTrail-org/LEANN).

## Policy

- Treat `.leann/` as generated local state. It must not be committed, copied
  into release bundles, or cited as manuscript evidence.
- Install LEANN at the user or agent level only. Do not add it to this
  repository's `pyproject.toml`, CI configuration, pipeline stages, or MCP
  configuration by default.
- Build indexes from tracked public files when working in the public template
  checkout. Avoid indexing private symlinked project mirrors through
  `template/projects/<name>`.
- Build private or rotating project indexes from the canonical private checkout,
  not from public-template symlinks.
- Use LEANN search results as navigation hints. Verify any claim with source
  files, tests, evidence registries, artifact manifests, ledgers, and validation
  commands.

## Optional Setup

Follow LEANN's current upstream installation instructions outside this
repository. The upstream README documents a `uv` environment and `uv pip install
leann` path; keep that environment separate from template's managed `uv` lock
unless a future task explicitly asks for integration.

Do not commit any MCP configuration. If a user explicitly requests LEANN MCP,
configure it in their user-level agent settings, then document the command that
was run in the task report.

## Template Root Index

Build from tracked files only:

```bash
leann build template-public --docs $(git ls-files)
```

Search the local index:

```bash
leann search template-public "where is AutoResearch readiness validated?"
```

List or remove local indexes:

```bash
leann list
leann remove template-public
```

If the tracked file list is too large for the shell, build a narrower local
index from the surfaces needed for the task:

```bash
leann build template-docs --docs README.md AGENTS.md CLAUDE.md docs infrastructure scripts
```

## Associated Projects

For private or rotating projects, work from the private project checkout itself:

```bash
cd "$TEMPLATE_PRIVATE_PROJECTS_ROOT/working/<project-name>"
leann build "<project-name>" --docs $(git ls-files)
```

Do not build from a symlinked path such as
`template/projects/working/<project-name>`. That keeps local retrieval separate
from the public repository confidentiality boundary.

## Guardrails

- `.gitignore` ignores `.leann/` at the root and nested project levels.
- `scripts/check_tracked_generated_artifacts.py` rejects tracked `.leann/*`
  files even if someone force-adds them.
- `scripts/check_tracked_projects.py` remains the separate guard for tracked
  non-template project paths.
- Search hits are discovery aids only; cite template source artifacts, not LEANN
  index output, in manuscript or publication claims.

Run the relevant guard slice after changing this guide or local-index policy:

```bash
uv run pytest tests/infra_tests/project/test_git_guards.py -q
uv run python scripts/check_tracked_generated_artifacts.py
uv run python scripts/check_tracked_projects.py
```
