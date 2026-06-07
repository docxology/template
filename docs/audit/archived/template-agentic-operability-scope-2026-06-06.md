# template/ agentic operability scope — 2026-06-06

## Purpose

This report records the completed review and improvement pass over root
`README.md`, root `AGENTS.md`, `infrastructure/`, `docs/`, and the immediately
related `projects/` lifecycle documentation for completeness, currency,
functional validation, and agentic discoverability via `SKILL.md` workflows.

The review focused on surfaces that agents actually consume:

- Root orientation: [`../../../README.md`](../../../README.md) and [`../../../AGENTS.md`](../../../AGENTS.md)
- Documentation hub: [`../../AGENTS.md`](../../AGENTS.md), [`../../documentation-index.md`](../../documentation-index.md), and [`../../_generated/skills_index.md`](../../_generated/skills_index.md)
- Workflow skills: [`../../prompts/SKILL.md`](../../prompts/SKILL.md), [`../../prompts/AGENTS.md`](../../prompts/AGENTS.md), and child skills
- Infrastructure skill hubs: [`../../../infrastructure/SKILL.md`](../../../infrastructure/SKILL.md) and [`../../../infrastructure/README.md`](../../../infrastructure/README.md)
- Project lifecycle docs: [`../../../projects/README.md`](../../../projects/README.md), [`../../../projects/AGENTS.md`](../../../projects/AGENTS.md), [`../../../projects/PAI.md`](../../../projects/PAI.md), and [`../../../projects/PROJECTS_PARADIGM.md`](../../../projects/PROJECTS_PARADIGM.md)
- Validation commands available through `infrastructure.skills`, `scripts/lint_docs.py`, and `infrastructure.core.health`

## Current validated state

### Passed gates after final edits

The following commands completed successfully after the documentation and
formatting updates in this pass:

```bash
uv run python scripts/lint_docs.py --json --repo-root .
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
uv run python -m infrastructure.skills check-all-exports
uv run pytest tests/infra_tests/skills -q
uv run python -m infrastructure.core.health --json --quiet
git diff --check -- README.md AGENTS.md STATUS.md docs/AGENTS.md docs/RUN_GUIDE.md docs/documentation-index.md docs/maintenance/README.md docs/prompts/AGENTS.md docs/security/secure_execution.md infrastructure/README.md infrastructure/SKILL.md projects/AGENTS.md projects/PAI.md projects/PROJECTS_PARADIGM.md projects/README.md projects/templates/template_textbook/src/textbook/content.py docs/audit/archived/template-agentic-operability-scope-2026-06-06.md
```

Observed results:

- Docs lint: 235 Mermaid blocks discovered, 0 broken links, 0 consistency issues, 0 doc-pair issues
- Skill manifest check: `ok`
- Workflow skill contracts: `skill contracts ok`
- `__all__` audit: `0 violations under infrastructure`
- Skill tests: 99 passed
- Full health gate: `"passed": true`
- `git diff --check` on the touched focused file set: no whitespace errors

### Project-focused validation completed

The previously interrupted focused active-inference validation was rerun to
completion:

```bash
uv run --directory projects/templates/template_active_inference \
  --with pytest --with pytest-cov --with pytest-timeout --with coverage==7.13.2 \
  --extra dev python -m pytest \
  tests/test_track_consolidation.py \
  tests/test_figures.py \
  tests/test_manuscript_variables.py \
  tests/test_si_statistics.py \
  -q --no-cov
```

Observed result: 28 collected, 28 passed in 265.84s.

### Formatting fixes applied by validation

Two formatting-only fixes were needed by health gates during this pass:

```bash
uv run ruff format \
  projects/templates/template_active_inference/src/manuscript/variables.py \
  projects/templates/template_active_inference/src/roadmap_tracks/sheaf_tracks.py \
  projects/templates/template_active_inference/src/roadmap_tracks/supplemental.py \
  projects/templates/template_active_inference/src/visualizations/figures.py \
  projects/templates/template_active_inference/src/visualizations/figures_sheaf_draw.py

uv run ruff format projects/templates/template_textbook/src/textbook/content.py
```

The second health run passed with `787 files already formatted`.

## Improvements completed in this pass

### Agentic SKILL discoverability

1. [`../../../README.md`](../../../README.md)
   - Added a root-level “Agentic operation and SKILLS” section.
   - Added direct routing from the assistant/editor note to [`../../prompts/SKILL.md`](../../prompts/SKILL.md) and [`../../_generated/skills_index.md`](../../_generated/skills_index.md).
   - Documented concrete maintenance commands for `write-index`, `write`, `check`, and `check-contracts`.

2. [`../../AGENTS.md`](../../AGENTS.md)
   - Updated the AI-agent entry path from only `rules/AGENTS.md` to:
     `prompts/SKILL.md → prompts/agentic-use/SKILL.md → rules/AGENTS.md`.

3. [`../../prompts/AGENTS.md`](../../prompts/AGENTS.md)
   - Added an explicit “Adding or changing a workflow skill” checklist.
   - The checklist now captures the expected synchronized edit set:
     child `SKILL.md`/`README.md`/`AGENTS.md`, hub `SKILL.md`, `MODE_REGISTRY.md`, human `README.md`, eval cases, generated skill artifacts, and final verification commands.
   - It also warns agents not to hand-edit `docs/_generated/skills_index.md` or `.cursor/skill_manifest.json`.

4. [`../../../infrastructure/SKILL.md`](../../../infrastructure/SKILL.md)
   - Added missing nested/first-party skill references:
     - `infrastructure/reference/citation/SKILL.md`
     - `infrastructure/reference/verification/SKILL.md`
     - `infrastructure/search/literature/SKILL.md`
     - `infrastructure/sia/SKILL.md`

5. [`../../../infrastructure/README.md`](../../../infrastructure/README.md)
   - Added the same missing skill rows so the human table matches live discovery.

### Private lifecycle wording synchronized

The docs now consistently distinguish:

1. Public rendered scope: `projects/templates/` plus optional `projects/active/`.
2. Required private sidecar signature: `working/` + `archive/`.
3. Supported optional lifecycle mirrors: `active/`, `published/`, and `other/` when present.
4. Non-rendered sidecar projects can be rendered explicitly with qualified names such as `working/<name>` without entering default discovery.

Files updated for this lifecycle sync:

- [`../../../AGENTS.md`](../../../AGENTS.md)
- [`../../../projects/AGENTS.md`](../../../projects/AGENTS.md)
- [`../../../projects/README.md`](../../../projects/README.md)
- [`../../../projects/PAI.md`](../../../projects/PAI.md)
- [`../../../projects/PROJECTS_PARADIGM.md`](../../../projects/PROJECTS_PARADIGM.md)
- [`../../RUN_GUIDE.md`](../../RUN_GUIDE.md)
- [`../../documentation-index.md`](../../documentation-index.md)
- [`../../maintenance/README.md`](../../maintenance/README.md)
- [`../../security/secure_execution.md`](../../security/secure_execution.md)
- [`../../../STATUS.md`](../../../STATUS.md)

The stale-lifecycle sweep now returns 0 hits for the targeted drift patterns:

```bash
rg -n "until moved into\s*`projects/`|until moved under `projects/active/`|Promote projects from|promoted to `projects/active/`|Move project from `projects/active|Move project from `projects/archive|mv projects/working/.*projects/active|mv projects/archive/.*projects/active|private repo.*active/working/published/archive/other|active/working/published/archive/other" . --glob '*.md'
```

### Permanent exemplar roster corrected where human docs enumerate it

`projects/README.md` and `projects/PAI.md` now include the full current public
exemplar roster, including the newer `template_autoscientists`,
`template_newspaper`, `template_sia`, and `template_textbook` entries. Where docs
should not enumerate rotating work, they point to generated facts instead.

## Worktree caveat

The worktree was already substantially dirty before this pass, and it remains
substantially dirty. This report does not classify unrelated pre-existing source,
project, or generated-output changes as safe to commit.

Notable broad dirty areas observed by `git status --short` include:

- generated outputs under `output/templates/*`
- many public exemplar project files under `projects/templates/*`
- `infrastructure/project/linking.py` and related project tests
- root and docs files touched by this audit pass
- untracked `docs/audit/archived/template-agentic-operability-scope-2026-06-06.md`
- untracked project/test files such as `projects/templates/template_active_inference/src/roadmap_tracks/visualization_audit.py` and `projects/templates/template_autoscientists/tests/test_manuscript_numbers.py`

Before staging, separate:

1. audit/docs/skill-routing changes,
2. formatting-only source changes,
3. unrelated project-source WIP,
4. generated `output/` churn.

Do not stage generated output blindly.

## Remaining recommended improvements

### R1 — classify generated-output churn

The `output/templates/*` tree is disposable generated output unless a release or
fixture update intentionally tracks it. Inspect before staging:

```bash
git status --short output/ | sed -n '1,160p'
git diff --stat -- output/
```

Acceptance criterion: generated output is either intentionally committed as part
of a release/update or restored/removed separately from source/docs.

### R2 — run public exemplar tests one project at a time

Because project test trees can each define `tests/conftest.py`, do not run all
project tests in one pytest process. Use one process per public exemplar.

Suggested loop:

```bash
for project in \
  template_active_inference \
  template_autoresearch_project \
  template_autoscientists \
  template_code_project \
  template_newspaper \
  template_prose_project \
  template_sia \
  template_template \
  template_textbook
do
  uv run python scripts/01_run_tests.py --project-only --project "$project" --verbose
done
```

Acceptance criterion: each project passes its own test gate, or each failure is
recorded with exact project, command, and first failing test.

### R3 — run core pipeline smoke on the stable exemplar

Use `template_code_project` as the stable control-positive exemplar:

```bash
./run.sh --pipeline --project template_code_project --core-only
```

Acceptance criterion:

- output validation passes or reports only documented non-blocking warnings
- PDF exists under `output/templates/template_code_project/pdf/`
- reports under `output/templates/template_code_project/reports/` are updated intentionally

### R4 — consider richer metadata contracts for infrastructure skills

Most `infrastructure/**/SKILL.md` files currently carry minimal YAML frontmatter
(`name`, `description`) rather than the richer `metadata.version`, tags, and
related-skill contract used by `docs/prompts/**/SKILL.md`.

This is currently accepted by the repository’s own skill checker, so it is not a
bug. If stronger cross-agent routing is desired, add an optional contract for
infrastructure skills in `infrastructure.skills.contracts` and migrate the
infrastructure skill files gradually while preserving backward compatibility.

## Summary verdict

The focused agentic-discoverability and lifecycle-clarity improvements requested
in this pass are complete and verified. The repo now has clearer SKILL routing,
a workflow-skill maintenance checklist, synchronized private-sidecar lifecycle
wording, and passing docs/skills/health gates.

The repository should still not be treated as clean-to-commit until unrelated
pre-existing source and generated-output changes are classified. The next safe
milestone is a staging review that separates human documentation changes from
format-only source changes and generated `output/` churn.
