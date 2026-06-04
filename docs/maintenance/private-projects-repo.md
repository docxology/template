# Private projects repo (`docxology/projects`) + lifecycle links

> Implemented 2026-05-21; lifecycle mirrors expanded 2026-05-24. This is the authoritative record of the private-projects-repo design (supersedes the original migration plan, now removed).

## Why

Confidential / rotating research projects must not live in this **public** repo.
They live in a separate **private** repo, `docxology/projects`, cloned as a
**sibling** of this one:

```
~/Documents/GitHub/
├── template/      (public  — this repo: pipeline + public exemplars)
└── projects/      (private — docxology/projects: active/ working/ published/ archive/ other/)
```

## The mechanism (symlink-in-place)

[`infrastructure/project/linking.py`](../../infrastructure/project/linking.py)
symlinks private lifecycle folders into local template mirrors:

| Private folder | Local mirror | Rendered by `run.sh`? |
| --- | --- | --- |
| `active/<name>` | `template/projects/active/<name>` | Yes |
| `working/<name>` | `template/projects/working/<name>` | No |
| `published/<name>` | `template/projects/published/<name>` | No |
| `archive/<name>` | `template/projects/archive/<name>` | No |
| `other/<name>` | `template/projects/other/<name>` | No |

> **Operator playbook (private side).** This page is the engine-side record of the
> *mechanism*. Operators who have the private sibling checked out keep their own
> operational playbook in that repo's `docs/` tree — a modular hub
> (`docs/lifecycle/`, `docs/publishing/`, `docs/rendering/`, each with
> `README.md` + `AGENTS.md`) covering lifecycle moves, the GitHub + Zenodo + DOI
> release/verification flow, and rendering. It signposts back into this `docs/`
> tree as canonical. It is intentionally **not linked here** (the private repo is
> absent from public clones).

Because `projects/` is a Python **namespace
package**, the symlink resolves transparently for `from projects.<name>.src…`
imports, `discover_projects`, `validate_project_structure`, and rendering — the
project behaves exactly like a native child of `projects/`. Execution stays in
this checkout, so `infrastructure/` resolves natively (**no submodule needed**).
The non-rendered mirrors (`working/`, `published/`, `archive/`, `other/`) are for
inspection and explicit local work only; default discovery scans only the
rendered subfolders `projects/templates/` and `projects/active/`.

`sync_private_project_links()` runs automatically in
`infrastructure/orchestration/cli.py` (`_maybe_sync_links`) on **every** `run.sh`
invocation. It is idempotent, a no-op when the private repo is absent (CI /
fresh public clone behave exactly as before), and best-effort (a sync failure
prints a warning, never crashes the CLI).

### Lifecycle

| Folder | Local visibility | Rendered by `run.sh`? | Operation to change |
|--------|------------------|----------------------|---------------------|
| `active/` | `projects/active/<n>` | **Yes, every run** | `mv working/<n> active/<n>` |
| `working/` | `projects/working/<n>` | No (backburner) | `mv active/<n> working/<n>` |
| `published/` | `projects/published/<n>` | No (shipped) | `mv active/<n> published/<n>` |
| `archive/` | `projects/archive/<n>` | No (retired) | `mv …/<n> archive/<n>` |
| `other/` | `projects/other/<n>` | No (misc) | `mv …/<n> other/<n>` |

Explicit re-sync without a full run: `uv run python -m infrastructure.orchestration link-projects`
(supports `--dry-run`, `--no-prune`).

### Configuring the private root

Resolution order: `$TEMPLATE_PRIVATE_PROJECTS_ROOT` → one-line
`template/.private_projects_root` (gitignored) → sibling `../projects`. The bare
sibling fallback requires the full `active/`+`working/`+`published/`+`archive/`+`other/`
signature so a coincidental sibling folder with only an `active/` child can't be mislinked.
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

- `check_tracked_projects.py` scans only `projects/`. The non-rendered subfolders
  (`working/`, `published/`, `archive/`, `other/`) are gitignored and non-rendered,
  but a future public archive policy should extend the guard before tracking
  anything under those subfolders.
- Public git **history** may contain intentionally-published dataset material
  (e.g. cogant Kaggle/HuggingFace prep). Audit history separately if any of it
  was sensitive — gitignore/guard only govern the current index.
