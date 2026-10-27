# template_code_executor

A **code_executor** exemplar tool executes trusted Python or shell code under the
current user and returns structured output. A bundled Python supervisor enforces
finite stdin/execution deadlines, captures at most 1 MiB per output stream, strips
credential-shaped environment names, and removes descendants that inherit its
private run marker, including detached sessions. An independent guardian also
cleans these descendants if the calling supervisor terminates.

This is host execution. Operating-system isolation and malicious code that
deliberately removes its inherited process identity require a separate sandbox.

## Files

```
template_code_executor/
├── tools.yaml           # Tool manifest
├── README.md            # This file
├── AGENTS.md            # Agent-oriented documentation
├── .gitignore
├── scripts/
│   ├── run.sh           # Thin execution entrypoint
│   └── validate.sh      # Manifest & environment validation
└── src/
    ├── code_executor.py # Deadline and output supervisor
    └── process_cleanup.py # Portable token-bound cleanup
```

## Quick Start

```bash
# Validate environment
bash scripts/validate.sh

# Run with a JSON payload on stdin
echo '{"code": "print(42)", "language": "python"}' | bash scripts/run.sh
```

The required runtime is POSIX Python >=3.14; set `TEMPLATE_PYTHON` to select an
installed interpreter. `jq` and GNU `timeout` are unnecessary. `timeout_s` must be
a finite positive number at most 300 (default 30). Incomplete stdin fails after
five seconds. `sh` and `bash` select the installed Bash runtime.

Outer exit 0 means the supervisor produced a result. Inspect `exit_code` for the
command outcome: 124 means its total deadline expired, and output overflow fails
with `output_truncated: true`. `child_exit_code` preserves the actual child exit
status, or null when no code was launched. Outer exit 2 indicates invalid input
or a supervision failure.

## Manifest (`tools.yaml`)

| Field | Value |
|---|---|
| type | `code_executor` |
| version | `1.0` |
| license | `CC0-1.0` |
| entrypoints | `scripts/run.sh`, `scripts/validate.sh` |

## Customising

Keep scripts thin; change execution policy in `src/`. Preserve finite deadlines,
the independent guardian, output bounds, real child status, and installed-wheel
resource parity when extending the tool. Run the pools exemplar's real process
controls before distributing it.
