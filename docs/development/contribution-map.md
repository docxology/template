# Contributor contribution map

Use this guide before starting a contribution. Its purpose is to reduce
duplicate work, keep changes small enough to review, and route ideas to the
right surface before code is written.

## First overlap check

Classify the idea before recommending an implementation:

| Classification | Meaning | Recommended response |
| --- | --- | --- |
| Built | The behavior already exists and is documented or tested. | Point to the command, API, doc, or test. Suggest docs/tests only if discovery is poor. |
| Partial | A working surface exists but has a known gap. | Contribute the smallest missing behavior, regression test, or doc clarification. |
| Proposed | The backlog, roadmap, issue tracker, or PRs already discuss it. | Align with that thread and avoid parallel design work. |
| Absent | No matching implementation, proposal, or active lane was found. | Choose the smallest useful contribution shape after checking ownership and risk. |

Run this minimum check before planning work:

```bash
git status --short --branch
git diff --name-only
git ls-files --others --exclude-standard
gh-axi pr list --limit 20
gh-axi issue list --limit 30
uv run python -m infrastructure.project.public_scope source-paths
uv run python -m infrastructure.skills operations-list-json
uv run python -m infrastructure.skills list-json
```

Then inspect the relevant backlog and docs:

- [`../../TO-DO.md`](../../TO-DO.md) for active backlog IDs and retired
  assumptions.
- [`roadmap.md`](roadmap.md) for longer-range direction.
- [`coverage-gaps.md`](coverage-gaps.md) for measured test targets and deliberate
  non-targets.
- [`code-review-checklist.md`](code-review-checklist.md) for merge criteria.
- [`../_generated/active_projects.md`](../_generated/active_projects.md) and
  [`../_generated/COUNTS.md`](../_generated/COUNTS.md) for public scope and
  measured facts.

For source changes, use the local graph/index tools when available, then read
the owning `AGENTS.md` in the directory being changed. Do not rely on a grep hit
alone when a function, CLI, operation, skill, or plugin surface may already own
the behavior.

## Useful contribution shapes

Low-risk first contributions:

- Fix stale docs by replacing copied counts or project rosters with links to the
  generated source of truth.
- Add focused documentation examples for an existing command, skill, operation,
  or validation gate.
- Add deterministic tests for a known branch in `coverage-gaps.md`, using real
  files, subprocesses, or local fixtures.
- Improve diagnostics or failure messages without changing successful behavior.

Medium-sized contributions:

- Close one `SCRIPTS-LOGIC-*` item at a time by moving inline script logic into
  the owning `infrastructure/` package and preserving command output.
- Add subprocess smoke coverage for CLI shims only when the command behavior
  changed.
- Improve skill or operation catalog documentation after confirming the
  generated manifests still match discovery.

Work that needs maintainer alignment before coding:

- Core changes to the pipeline DAG, public project discovery, generated-artifact
  policy, or confidentiality gates.
- New publishing destinations, credential flows, live network behavior, or
  autonomous public-write paths.
- Hermes A2A, gateway, or cross-agent runtime integration in core. Treat Hermes
  experience as useful for optional plugin/adapter guidance unless maintainers
  explicitly ask for a core runtime change.
- New default MCP servers, plugin protocols, or skills that affect every agent
  session.

Areas to avoid unless explicitly assigned:

- Active dirty lanes in `infrastructure/publishing/`,
  `infrastructure/validation/output/`,
  `projects/templates/template_gold_refinement/`, and
  `projects/templates/template_literature_meta_analysis/`.
- Generated outputs under `output/templates/` or project-local `output/` unless
  the matching source producer is being regenerated and verified.
- Dependency-update overlap with open PR
  [#32](https://github.com/docxology/template/pull/32), which currently tracks
  the `actions/checkout` bump to `7.0.0`.

## Extension surface routing

Prefer the narrowest surface that solves the problem:

| Idea shape | Usually best as |
| --- | --- |
| Existing workflow is hard to find | Documentation link, example, or checklist |
| Command works but lacks regression coverage | Focused subprocess or fixture test |
| Script contains reusable domain logic | `SCRIPTS-LOGIC-*` style infrastructure extraction |
| Agent workflow needs better instructions | `SKILL.md` update plus manifest regeneration |
| Optional external integration | Plugin, adapter, or guide before core coupling |
| Public output or release behavior | Maintainer-aligned core change with dry-run tests |

When a future idea is reviewed, answer in this order:

1. Whether it appears built, partial, proposed, or absent.
2. Where in the repo the overlap check looked.
3. Related PRs, issues, backlog IDs, docs, tests, or generated facts.
4. Likely maintainer expectation and compatibility risk.
5. The smallest mergeable contribution shape.
6. A focused implementation plan only after the overlap risk is checked.

## Current live signals

Last refreshed: 2026-06-27.

- GitHub issues: `0` open via `gh-axi issue list --limit 30`.
- GitHub PRs: `1` open, Dependabot PR #32 for `actions/checkout` `7.0.0`.
- Public source scope: `infrastructure` plus 13 public exemplar `src` trees via
  `uv run python -m infrastructure.project.public_scope source-paths`.
- Skills catalog: 56 entries via `uv run python -m infrastructure.skills list-json`.
- Operations catalog: 18 entries via
  `uv run python -m infrastructure.skills operations-list-json`.
- Package version and latest GitHub release: `3.5.1` / `v3.5.1`.

Refresh these before using them in a PR body or committing new roadmap text.
