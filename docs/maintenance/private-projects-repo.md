# Private projects repo (`docxology/projects`) + the active-link mechanism

> Implemented 2026-05-21. The authoritative record of the private-projects-repo design (supersedes the original migration plan, now removed).

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
symlinks every directory under the private repo's `active/` into
`template/projects/<name>`. Because `projects/` is a Python **namespace
package**, the symlink resolves transparently for `from projects.<name>.src…`
imports, `discover_projects`, `validate_project_structure`, and rendering — the
project behaves exactly like a native child of `projects/`. Execution stays in
this checkout, so `infrastructure/` resolves natively (**no submodule needed**).

`sync_active_links()` runs automatically in `infrastructure/orchestration/cli.py`
(`_maybe_sync_links`) on **every** `run.sh` invocation. It is idempotent, a
no-op when the private repo is absent (CI / fresh public clone behave exactly as
before), and best-effort (a sync failure prints a warning, never crashes the CLI).

### Lifecycle

| Folder | Rendered by `run.sh`? | Operation to change |
|--------|----------------------|---------------------|
| `active/` | **Yes, every run** (symlinked in) | `mv passive/<n> active/<n>` |
| `passive/` | No (backburner) | `mv active/<n> passive/<n>` (link auto-pruned) |
| `archive/` | No (retired) | `mv …/<n> archive/<n>` |

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
3. **`.gitignore`** — `projects/*` ignored except the two exemplars + `*.md`; the
   symlinks match `projects/*` and are never tracked.
4. **`scripts/check_tracked_projects.py`** — fails CI / pre-push if anything but
   the two exemplars is tracked under `projects/`.

### Self-versioned projects

Projects that are their own git repos (own remotes) are **gitignored by basename**
in the private repo (see its `.gitignore`) to avoid broken gitlinks; they keep
independent history on their own remotes. Their *uncommitted* working state is
backed up only when pushed to those remotes — push them to avoid single-disk risk.

## Known follow-ups

- `check_tracked_projects.py` scans only `projects/`. A force-add under
  `projects_in_progress/` or `projects_archive/` would not be caught. Both are
  now empty in this repo; consider extending the guard to cover them.
- Public git **history** may contain intentionally-published dataset material
  (e.g. cogant Kaggle/HuggingFace prep). Audit history separately if any of it
  was sensitive — gitignore/guard only govern the current index.
