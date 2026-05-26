# CodeGraph Local Index Guide

CodeGraph is an optional local code-intelligence index for agent-assisted
maintenance. It is useful for source-code questions such as "what calls this
function?", "which files are affected?", and "where does this workflow enter the
pipeline?" It is not a pipeline stage, a CI dependency, or manuscript evidence.

Official project: [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph).

## Policy

- Treat `.codegraph/` as generated local state. It must not be committed,
  copied into release bundles, or used as a source of publication facts.
- Install CodeGraph at the user or agent level. Do not add it to this
  repository's `pyproject.toml` dependency groups.
- Initialize the public template checkout from the template root. The root
  `.gitignore` keeps local/private symlinked project trees outside the index.
- Initialize private associated projects from their canonical private checkout,
  not through `template/projects/<name>` symlinks.
- Use CodeGraph for code navigation and impact analysis. Continue to verify
  claims with source files, tests, rendered artifacts, ledgers, and validation
  commands.

## Template Root

Print the recommended commands without requiring CodeGraph to be installed:

```bash
uv run python scripts/codegraph_local.py commands .
```

After installing CodeGraph, initialize and index the template root:

```bash
codegraph init "$(pwd)" --index
codegraph status "$(pwd)"
```

Verify that private/local project paths were not indexed:

```bash
codegraph files "$(pwd)" --json | uv run python scripts/codegraph_local.py verify-scope
```

This check allows `infrastructure/`, root docs, `projects/*.md`, and the public
template exemplars listed by `infrastructure.project.public_scope`. It fails if
the JSON file list contains a non-template path under `projects/`.

## Associated Projects

For a private or rotating project, work from the project repository itself:

```bash
cd /Users/4d/Documents/GitHub/projects/active/<project-name>
codegraph init "$(pwd)" --index
codegraph status "$(pwd)"
```

Do not initialize a private project through a public-template symlink such as
`template/projects/<project-name>`. That keeps local indexing independent from
the public repository's confidentiality boundary.

## Helper API

The modular implementation lives in `infrastructure.project.codegraph`.

| Helper | Use |
| --- | --- |
| `build_codegraph_init_command(path)` | Build the canonical `codegraph init <path> --index` command |
| `build_codegraph_files_command(path)` | Build the JSON file-list command used for scope checks |
| `verify_codegraph_scope_payload(payload)` | Return private/local project paths found in CodeGraph file JSON |
| `unexpected_indexed_project_paths(paths)` | Validate a plain path list against the public project allowlist |

The script wrapper `scripts/codegraph_local.py` only prints commands or runs the
scope verifier; it delegates all behavior to the package module.

## Guardrails

- `.gitignore` ignores `.codegraph/` at the root and nested project levels.
- `scripts/check_tracked_generated_artifacts.py` rejects tracked
  `.codegraph/*` files even if someone force-adds them.
- `scripts/check_tracked_projects.py` remains the separate confidentiality
  guard for tracked project paths.

Run the relevant guard slice after changing this integration:

```bash
uv run pytest tests/infra_tests/project/test_codegraph.py tests/infra_tests/project/test_git_guards.py -q
uv run python scripts/check_tracked_generated_artifacts.py
uv run python scripts/check_tracked_projects.py
```
