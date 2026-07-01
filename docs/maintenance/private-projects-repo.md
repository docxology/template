# Private projects repo (`docxology/projects`) + lifecycle links

> Implemented 2026-05-21; simplified sidecar signature updated 2026-06-06.
> This is the engine-side record of the private-projects-repo design.

## Why

Confidential / rotating research projects must not live in this public repo.
They live in a separate private repo, `docxology/projects`, cloned as a sibling:

```text
~/Documents/GitHub/
├── template/      public  — this repo: pipeline + public exemplars
└── projects/      private — docxology/projects: working/ + archive/
```

The sidecar no longer carries a copied `template/` project. The canonical
meta-template lives in this public repo at
[`projects/templates/template_template/`](../../projects/templates/template_template/).

## The mechanism (symlink-in-place)

[`infrastructure/project/linking.py`](../../infrastructure/project/linking.py)
mirrors existing private lifecycle folders into local template mirrors:

| Private folder | Local mirror | Rendered by default? |
| --- | --- | --- |
| `working/<name>` | `template/projects/working/<name>` | No; explicit `working/<name>` commands only |
| optional `ongoing/<name>` | `template/projects/ongoing/<name>` | No; long-lived, no publication target — explicit `ongoing/<name>` commands only |
| `archive/<name>` | `template/projects/archive/<name>` | No |
| optional `active/<name>` | `template/projects/active/<name>` | Yes, if deliberately reintroduced |
| optional `published/<name>` | `template/projects/published/<name>` | No |
| optional `other/<name>` | `template/projects/other/<name>` | No |

Because `projects/` is a Python namespace package, symlinks resolve
transparently for imports, project-root resolution, validation, and rendering.
Execution stays in this checkout, so `infrastructure/` resolves natively.

**Category groupings (one level deep).** Within a lifecycle folder, a private
child directory named with a leading underscore is a *category*, not a
project: its own children mirror as `projects/<lifecycle>/_<category>/<name>`
instead of a flat `projects/<lifecycle>/<name>`. For example
`archive/_legal/foo_project` mirrors to
`template/projects/archive/_legal/foo_project`. Nesting stops at one level —
a category's children are never themselves treated as categories — and
ungrouped entries stay flat. The underscore prefix also sorts categories ahead
of plain lowercase project names in a directory listing. `link-projects`
prunes stale nested links the same as flat ones and removes an emptied
category directory.

The normal sidecar workflow is explicit rendering of `working/<name>` projects:

```bash
uv run python -m infrastructure.orchestration link-projects --dry-run
uv run python -m infrastructure.orchestration link-projects
uv run python scripts/03_render_pdf.py --project working/<name>
uv run python scripts/maintenance/rerender_working_pdfs.py --project <name>
```

Default discovery still scans the public exemplars under `projects/templates/`
and any optional `projects/active/` hot-seat entries. It does not run all
`working/` or `archive/` projects.

## Private-root resolution

Resolution order: `$TEMPLATE_PRIVATE_PROJECTS_ROOT` → one-line
`.private_projects_root` (gitignored) → sibling `../projects`.

Explicit env/config roots are accepted when they contain at least one supported
lifecycle folder. The bare sibling fallback requires the simplified
`working/` + `archive/` signature so a coincidental sibling `projects/` directory
cannot be mislinked. Disable auto-sync with `TEMPLATE_SKIP_LINK_SYNC=1`.

## Confidentiality model (defense in depth)

1. **Physical separation** — confidential content lives only in the private repo.
2. **Symlink boundary** — git refuses to stage content beyond a symbolic link.
3. **`.gitignore`** — `projects/*` ignored except public exemplars + root docs.
4. **`scripts/check_tracked_projects.py`** — fails CI/pre-push if anything but
   public exemplars is tracked under `projects/`.

## Self-versioned projects

Projects with their own remotes are represented inside `docxology/projects` as
lifecycle entries/symlinks to their canonical checkout. Commit their content to
their own remotes; the sidecar tracks placement, not duplicated payload.

## Operator playbook

Operators who have the private sibling checked out keep the private-side
playbook in that repo's `docs/` tree. This public page documents only the engine
mechanism and must not expose private project rosters.
