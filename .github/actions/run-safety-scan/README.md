# run-safety-scan

Composite action: the repository's single definition of the code-safety scan.

```yaml
- uses: ./.github/actions/run-safety-scan        # ci.yml defaults
  with:
    bandit-targets: infrastructure scripts projects   # default
    no-mocks: "true"                                  # default
```

[`scan.sh`](scan.sh) launches each gate in the background, keeps a separate log
per command, waits for every child, and exits non-zero if any of them failed:

| Gate | Command |
| --- | --- |
| Bandit MEDIUM+ | `uv run bandit -c bandit.yaml -r -ll <targets>` (`-c bandit.yaml` supplies the documented exclusion/allow-list policy) |
| no-mocks policy | `uv run python scripts/audit/verify_no_mocks.py` |

Callers:

| Caller | Inputs | Why |
| --- | --- | --- |
| [`ci.yml`](../../workflows/ci.yml) `lint` job (through [`run-public-lint`](../run-public-lint/action.yml)) | `safety-scan: true` there | The required PR gate has no other copy of the scan, so it joins the Ruff/type wave. |
| `ci.yml` standalone use | defaults | Same commands, its own step. |
| [`hardening.yml`](../../workflows/hardening.yml) `security` job | `bandit-targets` from the Source-derived public roster, `no-mocks: "false"` | The security job owns Bandit; the sibling `verify-no-mocks` job keeps the policy gate and branch-protection name. |

The LOW-severity `B602/B604/B605/B609` sweep in `hardening.yml` stays inline: it
selects different tests at a different severity, so it is a different gate.

## Editing

- The pin for `bandit.yaml` lives in the repository root; this action only
  supplies the invocation.
- Keep every gate blocking: a skipped child would make the aggregate exit status
  lie about what ran.
- Run `actionlint` after edits, and keep the sibling README/AGENTS pair current.
