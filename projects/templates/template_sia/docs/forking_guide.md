# Forking guide — template_sia

> Copy this exemplar when you need a deterministic SIA-style harness with
> public/private task splits and optional live self-improvement.

## TL;DR

```bash
NEW=my_sia_task
uv run python scripts/audit/copy_exemplar.py \
  --source templates/template_sia \
  --dest "projects/working/$NEW" \
  --new-name "$NEW"
# Edit manuscript/config.yaml (title, project_config.sia.task_name)
# Replace tasks/mini_classify/ with your task tree
# Record fixtures under src/fixtures/recorded_generations/ for CI replay
uv run pytest "projects/working/$NEW/tests/" --cov="projects/working/$NEW/src" --cov-fail-under=90
```

Private work stays under `projects/working/` (local-only). Promote to `projects/active/` in your private repo when ready to render — see [`docs/maintenance/private-projects-repo.md`](../../../../docs/maintenance/private-projects-repo.md).

## REQUIRED vs AESTHETIC

| Path | Status |
| --- | --- |
| `src/loop.py`, `src/reports.py`, `src/loop_config.py` | REQUIRED |
| `tasks/<name>/` with public/private split | REQUIRED |
| `src/fixtures/recorded_generations/` | REQUIRED for default CI replay |
| `scripts/run_sia_loop.py`, `scripts/z_generate_manuscript_variables.py` | REQUIRED |
| `tests/` | REQUIRED (90% gate) |
| `manuscript/config.yaml`, `manuscript/*.md`, `references.bib` | REQUIRED |
| `docs/*.md` | AESTHETIC (load-bearing for agents) |
| `domain_profile.yaml`, `experiment_plan.yaml` | REQUIRED forkability overlays |

## Post-fork steps

1. Register a new task and validate layout with `infrastructure.sia.cli validate`.
2. Run one live generation locally; capture artifacts into fixtures if you want CI replay.
3. Update manuscript tokens and methodology to describe your task — not upstream paper numbers.
4. Run full core pipeline before claiming publication readiness.

## Approval boundary for real mutation forks

The public exemplar never applies generated feedback to target code. A fork
that wants to apply mutations must produce a versioned
`src/approval.py::ApprovalContract` payload first:

1. run the target in a disposable sandbox;
2. record a SHA-256 digest of the proposed diff and a rollback snapshot;
3. inspect the diff and evaluation receipt;
4. obtain an owner approval receipt with a stable ID; and
5. apply only when the payload is `mode: live_apply` with
   `approval_status: approved`.

Missing sandbox, diff, rollback, or approval evidence is a hard failure. A
fixture replay uses `mode: fixture_replay` and must not claim human approval.
This separation keeps the public harness deterministic and makes a real fork's
state-changing authority auditable rather than inferred from a local test run.

## See also

- [`../../../../docs/guides/fork-an-exemplar.md`](../../../../docs/guides/fork-an-exemplar.md)
- [`../../../../docs/guides/new-project-setup.md`](../../../../docs/guides/new-project-setup.md)
