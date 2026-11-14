# Forking an Exemplar

Use this guide when you want a clean project seed from one of the public
`projects/templates/` exemplars without copying local caches, virtual
environments, rendered outputs, or stale package metadata.

## Pick the right exemplar

Start with `template_code_project` for the basic computational walkthrough.
Choose a domain-specific seed from the generated
[all-public exemplar differentiation map](../_generated/exemplar_roster.md),
then read that project's `README.md` and `STANDALONE.md` for its actual
dependencies and claim boundaries. The permanent public roster is owned by
[`active_projects.md`](../_generated/active_projects.md), not a second manual
table here. Measured counts and coverage are retained in
[`COUNTS.md`](../_generated/COUNTS.md).

## Clean copy

From a [prepared template checkout](startup-and-setup.md), at the repository root:

```bash
uv run --no-sync --offline python scripts/audit/copy_exemplar.py \
  --source templates/template_code_project \
  --dest projects/working/my_project \
  --new-name my_project \
  --author-name "Ada Lovelace" --author-email ada@example.org
```

Change `--source` to any `templates/<name>` from the table above. The helper
copies tracked source files plus non-ignored new source files, excludes local
artifacts (`.venv/`, caches, `htmlcov/`, `output/`, egg-info, `.DS_Store`, Lean
build products), and substitutes the exemplar slug in UTF-8 text files only.
Binaries are copied byte-for-byte.

The helper owns the fork's identity and export manifest; a raw `rsync` copy is
not equivalent. `--dry-run` previews the files without writing.

- `--new-name` rewrites the project slug in paths, package metadata and
  configuration; suffixed identifiers such as `<slug>_extra` are left alone.
- `--author-name` / `--author-email` replace the source author and remove the
  exemplar's DOI, ORCID, repository URL and release-date identity. A fork must
  not claim the source exemplar's publication.
- `--sdk-source path:<dir>` selects a checkout, `url:<git-or-file-url>` an
  explicitly available provider, and `version-only` the declared version from
  an actually available package source. Inside this checkout the helper derives
  the correct relative path automatically; outside it, nominate the real
  provider rather than an arbitrary ancestor.
- `--project-only` omits declared cross-root resource copies. It does not remove
  an SDK dependency or make missing DATA/resource prerequisites optional.

The default export writes `.template-export.json`, binding copied bytes,
resource dependencies and the original Source commit. Installed and mirror
acceptance consume this manifest; its existence alone is not acceptance.

## Forkability contract

Every public exemplar now ships:

- A top-level `STANDALONE.md` with purpose, clean-copy command, required edits,
  validation commands, intentional dependencies, and claim boundaries.
- `domain_profile.yaml` and `experiment_plan.yaml` overlays that validate with
  the shared loaders.
- Project-local `README.md` and `AGENTS.md`, plus fit-for-purpose docs where the
  exemplar needs them. The old 12-file docs hub is not a universal requirement.
- Independent project tests. Run one project test directory per pytest process;
  do not point pytest at all `projects/*/tests/` in one invocation.

The copied path under `projects/working/` is local-only. Only public exemplars
under `projects/templates/` are tracked in this public repository; the guard in
[`scripts/audit/check_tracked_all.py`](../../scripts/audit/check_tracked_all.py)
blocks accidental commits of non-template project trees.

## Validate the fork

Prepare the copied project's declared environment before executing its tests.
For the checkout-local copy above, from the repository root:

```bash
uv sync --project projects/working/my_project --extra dev \
  --python "$PWD/.venv/bin/python"
uv run --no-sync --offline --project projects/working/my_project \
  python -m pytest projects/working/my_project/tests/ \
  --cov=projects/working/my_project/src --cov-fail-under=90
```

This prepares the new fork's identity and lock; canonical unchanged exemplars
use `--locked`. For an independent export, follow its `README.md` / `STANDALONE.md`
and the [shared preparation boundary](../../projects/README.md#run-surface).
Formal tools, Advanced's Meta provider, admitted Root DATA and resource bundles
remain explicit project-specific prerequisites. A selected test run is not
whole native or publication acceptance.

`uv run python scripts/audit/check_template_drift.py --strict` validates the canonical
public exemplars under `projects/templates/`; run it before changing upstream
exemplars, not as proof that an arbitrary `projects/working/<name>/` fork is
schema-complete.

Some exemplars intentionally depend on shared `infrastructure/` modules; those
are forkable inside a full template checkout unless the fork vendors or replaces
the adapters. `template_template` is standalone only when it can inspect a
template-like checkout. `template_textbook` intentionally keeps stub markers
until an author fills the book.

## See also

- [`new-project-setup.md`](new-project-setup.md)
- [`../core/how-to-use.md`](../core/how-to-use.md)
- [`../RUN_GUIDE.md`](../RUN_GUIDE.md)
- [`../_generated/COUNTS.md`](../_generated/COUNTS.md)
