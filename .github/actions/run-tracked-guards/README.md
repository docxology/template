# run-tracked-guards

Composite action: the three "what is actually tracked" guards, defined once and
shared by both workflows.

```yaml
- uses: ./.github/actions/run-tracked-guards
```

| Guard | Command | Rejects |
| --- | --- | --- |
| Confidentiality | `uv run python scripts/audit/check_tracked_all.py` | any tracked path outside the public allowlists for `projects/`, `fonds/`, `rules/`, `tools/` |
| Secrets | `uv run python scripts/audit/check_tracked_secrets.py` | tracked high-confidence credential material |
| Generated artifacts | `uv run python scripts/audit/check_tracked_generated_artifacts.py` | generated outputs and local indexes that must stay untracked |

The guards run **sequentially**: each one reports its own named failure, and a
later guard never masks an earlier one. They are cheap (index reads plus a
bounded tree scan), so parallelising them buys nothing measurable and would make
the failure report ambiguous.

Callers: the `lint` job of [`ci.yml`](../../workflows/ci.yml) (required PR gate)
and the `lint` job of [`hardening.yml`](../../workflows/hardening.yml) (optional
exhaustive lane).

## Editing

- Keep the order above; `check_tracked_all.py` is the widest scope and fails
  first on a private path.
- A new tracked-tree guard belongs here only if both workflows must run it; a
  lane-specific guard stays in its workflow.
- Run `actionlint` after edits and keep the sibling README/AGENTS pair current.
