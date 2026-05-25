# Private projects repo (`docxology/projects`) + lifecycle links

> Implemented 2026-05-21; lifecycle mirrors expanded 2026-05-24. This is the authoritative record of the private-projects-repo design (supersedes the original migration plan, now removed).

## Why

Confidential / rotating research projects must not live in this **public** repo.
They live in a separate **private** repo, `docxology/projects`, cloned as a
**sibling** of this one:

```
~/Documents/GitHub/
├── template/      (public  — this repo: pipeline + 2 exemplars)
└── projects/      (private — docxology/projects: active/ passive/ archive/)
```

## The mechanism (symlink-in-place)

[`infrastructure/project/linking.py`](../../infrastructure/project/linking.py)
symlinks private lifecycle folders into local template mirrors:

| Private folder | Local mirror | Rendered by `run.sh`? |
| --- | --- | --- |
| `active/<name>` | `template/projects/<name>` | Yes |
| `passive/<name>` | `template/projects_in_progress/<name>` | No |
| `archive/<name>` | `template/projects_archive/<name>` | No |

Because `projects/` is a Python **namespace
package**, the symlink resolves transparently for `from projects.<name>.src…`
imports, `discover_projects`, `validate_project_structure`, and rendering — the
project behaves exactly like a native child of `projects/`. Execution stays in
this checkout, so `infrastructure/` resolves natively (**no submodule needed**).
The passive/archive mirrors are for inspection and explicit local work only;
default discovery still scans `projects/`, not the dormant mirrors.

`sync_private_project_links()` runs automatically in
`infrastructure/orchestration/cli.py` (`_maybe_sync_links`) on **every** `run.sh`
invocation. It is idempotent, a no-op when the private repo is absent (CI /
fresh public clone behave exactly as before), and best-effort (a sync failure
prints a warning, never crashes the CLI).

### Lifecycle

| Folder | Local visibility | Rendered by `run.sh`? | Operation to change |
|--------|------------------|----------------------|---------------------|
| `active/` | `projects/<n>` | **Yes, every run** | `mv passive/<n> active/<n>` |
| `passive/` | `projects_in_progress/<n>` | No (backburner) | `mv active/<n> passive/<n>` |
| `archive/` | `projects_archive/<n>` | No (retired) | `mv …/<n> archive/<n>` |

Explicit re-sync without a full run: `uv run python -m infrastructure.orchestration link-projects`
(supports `--dry-run`, `--no-prune`).

### Configuring the private root

Resolution order: `$TEMPLATE_PRIVATE_PROJECTS_ROOT` → one-line
`template/.private_projects_root` (gitignored) → sibling `../projects`. The bare
sibling fallback requires the full `active/`+`passive/`+`archive/` signature so a
coincidental sibling folder with only an `active/` child can't be mislinked.
Disable auto-sync with `TEMPLATE_SKIP_LINK_SYNC=1`.

## Confidentiality model (defense in depth)

1. **Physical separation** — confidential content lives only in the private repo.
2. **The symlink boundary** — git **refuses to stage content "beyond a symbolic
   link,"** so nothing inside a linked project can be added to this repo's index
   (stronger than gitignore).
3. **`.gitignore`** — `projects/*` ignored except public exemplars + `*.md`; the
   public repo never tracks private lifecycle symlinks or private payloads.
4. **`scripts/check_tracked_projects.py`** — fails CI / pre-push if anything but
   the public exemplars is tracked under `projects/`.

### Self-versioned projects

Projects that are their own git repos (own remotes) have copied directory
payloads ignored by basename in the private repo (see its `.gitignore`) to avoid
broken gitlinks or duplicated content; they keep independent history on their own
remotes. Their *uncommitted* working state is backed up only when pushed to those
remotes — push them to avoid single-disk risk.
Represent them inside `docxology/projects` as lifecycle symlinks to the sibling
canonical repo checkout (for example `projects/active/AGEINT -> ../../AGEINT`), not
as copied trees. Those symlink pointers can be tracked in the private repo, and
the template linker resolves them the same way it resolves native private-project
directories.

## Known follow-ups

- `check_tracked_projects.py` scans only `projects/`. The passive/archive mirrors
  are gitignored and non-rendered, but a future public archive policy should
  extend the guard before tracking anything under `projects_in_progress/` or
  `projects_archive/`.
- Public git **history** may contain intentionally-published dataset material
  (e.g. cogant Kaggle/HuggingFace prep). Audit history separately if any of it
  was sensitive — gitignore/guard only govern the current index.
