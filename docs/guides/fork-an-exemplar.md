# Forking an Exemplar

> The 5-minute "I just `git clone`d, where do I start?" path. Picks
> whichever canonical exemplar matches your work — numerical research,
> editorial review, or deterministic AutoResearch — and gets you to
> first-test-passing.

## Pick the right exemplar

| Your work shape | Fork this exemplar | Detailed walkthrough |
|---|---|---|
| Deterministic plan/evidence/claim/artifact readiness loops | [`projects/template_autoresearch_project/`](../../projects/template_autoresearch_project/) — AutoResearchClaw-inspired readiness checks without autonomous research execution; live test count + coverage in [`canonical_facts.md`](../_generated/canonical_facts.md) | [`README.md`](../../projects/template_autoresearch_project/README.md) |
| Numerical / algorithmic research with figures, dashboards, manuscript | [`projects/template_code_project/`](../../projects/template_code_project/) — has its own gradient-descent algorithm in `src/optimizer.py`, six figure generators in `src/figures/`; live test count + coverage in [`canonical_facts.md`](../_generated/canonical_facts.md) | [`forking_guide.md`](../../projects/template_code_project/docs/forking_guide.md) |
| Editorial / prose review pipeline — readability, structure, BibTeX validation | [`projects/template_prose_project/`](../../projects/template_prose_project/) — no algorithm of its own; `src/pipeline/` delegates to `infrastructure/prose/` + `infrastructure/reference/citation/`; live test count + coverage in [`canonical_facts.md`](../_generated/canonical_facts.md) | [`forking_guide.md`](../../projects/template_prose_project/docs/forking_guide.md) |

The walkthroughs follow the same shape: 4-line copy-paste TL;DR (`cp -r`
+ `sed` rename + `uv run pytest`), an explicit statement of the
confidentiality invariant, a REQUIRED-vs-AESTHETIC inventory, four
post-fork steps, and a friction-point table. Each guide ~150 lines.

## The contract a forker is signing onto

Forks of the public exemplars inherit four invariants the template gates
mechanically (the rest is convention). The project docs state these explicitly;
cross-referenced here for the impatient:

1. **Coverage gate** — `projects/{name}/src/` ≥ 90 % line+branch. Enforced by
   the matrix CI job and by the per-project `pyproject.toml`.
2. **Zero-mock policy** — no `unittest.mock` / `MagicMock` / `@patch` /
   `create_autospec` anywhere in `tests/`. Enforced by the drift
   checker (`mock_in_tests` detector) and a repo-level pre-commit grep.
3. **Confidentiality invariant** — only the public canonical exemplars from
   `infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES` under
   `projects/` are ever git-tracked.
   Any other fork is local-only, blocked from `git push` by
   [`scripts/check_tracked_projects.py`](../../scripts/check_tracked_projects.py)
   wired into `pre-push-quick`.
4. **Thin-orchestrator rule** — `scripts/` must call into `src/` and
   `infrastructure/`, never inline math/regex/parsing. Detected by
   audit (and the per-subdir `CONVENTIONS.md` documents the rule).

## Verify your fork is honest — the drift checker

The template ships a drift checker at
[`scripts/check_template_drift.py`](../../scripts/check_template_drift.py):
**9 detectors per exemplar** plus **2 repo-level checks** (hard-coded doc
counts and thin-orchestrator script enforcement). Unit tests at
[`tests/infra_tests/test_check_template_drift.py`](../../tests/infra_tests/test_check_template_drift.py).
While the checker today runs against the public canonical exemplars (not
arbitrary forks), it is the right model for the kind of self-check your
fork should grow into. Detectors:

| Rule | Catches |
|---|---|
| `function_name_drift` | docs reference a `_check_<name>` that no longer exists in `src/pipeline/checks.py` or `src/pipeline.py` |
| `test_class_drift` | docs reference a `TestXxx` that no longer exists in `tests/` |
| `__all___doc_drift` | `src/STYLE.md` or `docs/AGENTS.md` ships an `__all__` block that disagrees with `src/__init__.py` |
| `coverage_floor_drift` | docs claim a `fail_under = N` value that disagrees with `pyproject.toml` |
| `dead_link` | local markdown link target file doesn't exist (skips fenced-code examples and `new_*`/`my_*`/`your_*` example filenames) |
| `oversize_src_file` | any `src/*.py` over 1,500 lines (a refactor smell) |
| `blanket_except` | `except Exception` in `src/*.py` without a `noqa: BLE001` justification |
| `mock_in_tests` | mock primitives in `tests/` |
| `missing_canonical_file` | the ten files every exemplar must ship |

A WARNING-rated `except Exception` block whose surrounding comment
contains `TOP-LEVEL MAIN SAFETY NET` / `safety net` / `final handler` /
`top-level main` is exempted — narrowing such handlers replaces honest
breadth with silent gaps.

## What changed recently (May 2026 hardening)

Five things landed during the May 2026 audit pass that a forker
benefits from but might not discover from the older docs:

1. `template_code_project/src/analysis.py` was split into
   `src/analysis/` (orchestration) and `src/figures/` (the six
   `generate_*` plot functions). `src/analysis/__init__.py`
   re-exports the public analysis names via a try/except
   shim — your `from src.analysis import generate_convergence_plot`
   keeps working.
2. `template_prose_project/src/config.py` now **strictly** rejects
   unknown YAML keys at top-level + under `prose`/`bibliography`/`report`,
   and enforces invariants (`target_grade_level_min <
   target_grade_level_max`, `long_sentence_threshold > 0`,
   `citation_density_min_per_1000 ≥ 0`).
3. Sibling-parity files (`src/STYLE.md`, `tests/PATTERNS.md`,
   `scripts/CONVENTIONS.md`) now ship in the code and prose exemplars. They are
   recommended, not mandatory; the drift checker only gates `AGENTS.md`
   + `README.md`.
4. `scripts/check_template_drift.py` was added with 9 detectors and
   20 self-tests.
5. `scripts/00_preflight.py` was added to the code and prose exemplars — emits an
   actionable warning before the PDF stage if `chrome-headless-shell`
   is missing from the Puppeteer cache.

## See also

- [`new-project-setup.md`](new-project-setup.md) — older walkthrough; the
  per-project docs supersede it for the public canonical exemplars
- [`../core/how-to-use.md`](../core/how-to-use.md) — 12-skill-level
  usage guide
- [`../RUN_GUIDE.md`](../RUN_GUIDE.md) — pipeline orchestration
  reference (menu mapping, stage list, environment variables)
- [`../_generated/canonical_facts.md`](../_generated/canonical_facts.md)
  — live test counts, coverage percentages, active project roster
