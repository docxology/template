# Forking an Exemplar

Use this guide when you want a clean project seed from one of the public
`projects/templates/` exemplars without copying local caches, virtual
environments, rendered outputs, or stale package metadata.

## Pick the right exemplar

| Your work shape | Fork this exemplar | Standalone notes |
|---|---|---|
| Multi-track active-inference research with sheaf composition | [`template_active_inference`](../../projects/templates/template_active_inference/) | [`STANDALONE.md`](../../projects/templates/template_active_inference/STANDALONE.md) |
| Bounded AutoResearch loop with evidence/artifact gates | [`template_autoresearch_project`](../../projects/templates/template_autoresearch_project/) | [`STANDALONE.md`](../../projects/templates/template_autoresearch_project/STANDALONE.md) |
| Coordination-mechanism ablations for agent teams | [`template_autoscientists`](../../projects/templates/template_autoscientists/) | [`STANDALONE.md`](../../projects/templates/template_autoscientists/STANDALONE.md) |
| Code-driven computational research | [`template_code_project`](../../projects/templates/template_code_project/) | [`STANDALONE.md`](../../projects/templates/template_code_project/STANDALONE.md) |
| Conditional token-injection manuscripts | [`template_madlib`](../../projects/templates/template_madlib/) | [`STANDALONE.md`](../../projects/templates/template_madlib/STANDALONE.md) |
| Data-driven newspaper or print-layout engine | [`template_newspaper`](../../projects/templates/template_newspaper/) | [`STANDALONE.md`](../../projects/templates/template_newspaper/STANDALONE.md) |
| Manuscript-focused prose review | [`template_prose_project`](../../projects/templates/template_prose_project/) | [`STANDALONE.md`](../../projects/templates/template_prose_project/STANDALONE.md) |
| Self-improvement-agent fixture/live harness | [`template_sia`](../../projects/templates/template_sia/) | [`STANDALONE.md`](../../projects/templates/template_sia/STANDALONE.md) |
| Meta-research over a template-like checkout | [`template_template`](../../projects/templates/template_template/) | [`STANDALONE.md`](../../projects/templates/template_template/STANDALONE.md) |
| Book-length fillable scaffold | [`template_textbook`](../../projects/templates/template_textbook/) | [`STANDALONE.md`](../../projects/templates/template_textbook/STANDALONE.md) |

For one-glance differentiation, see the generated
[`docs/_generated/exemplar_roster.md`](../_generated/exemplar_roster.md).
Measured test counts and coverage live in
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md).

## Clean copy

From the repository root:

```bash
uv run python scripts/copy_exemplar.py \
  --source templates/template_code_project \
  --dest projects/working/my_project \
  --new-name my_project
```

Change `--source` to any `templates/<name>` from the table above. The helper
copies tracked source files plus non-ignored new source files, excludes local
artifacts (`.venv/`, caches, `htmlcov/`, `output/`, egg-info, `.DS_Store`, Lean
build products), and substitutes the exemplar slug in UTF-8 text files only.
Binaries are copied byte-for-byte.

Fallback when the helper is unavailable:

```bash
rsync -a \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
  --exclude 'htmlcov/' --exclude 'output/' --exclude 'rendered/' --exclude '*.egg-info/' \
  --exclude '.DS_Store' --exclude '.lake/' --exclude 'lake-packages/' \
  projects/templates/template_code_project/ projects/working/my_project/
```

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
[`scripts/check_tracked_projects.py`](../../scripts/check_tracked_projects.py)
blocks accidental commits of non-template project trees.

## Validate the fork

Use the `STANDALONE.md` file in the chosen exemplar for exact commands. The
common starting point for a copied project under `projects/working/<name>/` is:

```bash
uv run pytest projects/working/<name>/tests/ \
  --cov=projects/working/<name>/src --cov-fail-under=90
```

`uv run python scripts/check_template_drift.py --strict` validates the canonical
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
