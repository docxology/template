# AGENTS.md — template_code_executor

> Agent-oriented documentation for the `code_executor` exemplar tool.
> Human developers: see [README.md](README.md).

## Identity

- **Type:** `code_executor`
- **Manifest:** `tools.yaml`
- **Version:** `1.0`

## Invocation

### Run

```
stdin:  JSON object { "code": string, "language": string, "timeout_s": int? }
stdout: JSON object { "exit_code": int, "child_exit_code": int|null,
                     "timed_out": bool, "output_truncated": bool,
                     "stdout": string, "stderr": string }
exit:   0 = execution completed (check inner exit_code for code result)
        2 = executor error (malformed input, environment failure)
```

```bash
echo '{"code": "print(42)", "language": "python"}' | bash scripts/run.sh
```

### Validate

```
stdin:  (none)
stdout: human-readable validation report
exit:   0 = environment is valid and ready
        1 = validation failed (details on stdout)
```

```bash
bash scripts/validate.sh
```

## Agent Decision Guidance

- Use this tool when a task requires **executing code** and capturing output.
- Prefer `validate.sh` before `run.sh` in new environments to confirm dependencies are present.
- Always check the inner `exit_code` in the JSON result — outer exit 0 means the executor ran, not that the code succeeded.
- Execute only trusted code under the current user. This tool supplies process
  supervision; operating-system isolation is a separate responsibility.
- Do not include credentials in code or inputs. Credential-shaped environment
  names are stripped before starting code.
- Descendant cleanup relies on trusted subprocesses retaining their exact
  inherited run marker. Test detached sessions and calling-parent termination.
- Keep computation in the bundled `src/` supervisor and scripts thin.

## Dependencies

| Dependency | Purpose | Required |
|---|---|---|
| `bash` ≥ 3.2 | Script runtime | Yes |
| POSIX Python >=3.12 | JSON, deadlines, independent process guardian | Yes |

Set `TEMPLATE_PYTHON` to an explicitly selected installed interpreter. The tool
does not acquire runtimes. The finite execution budget is at most 300 seconds;
stdin and output have separate byte/deadline limits. Real controls live in
`projects/templates/template_pools_rules_tools/tests/test_code_executor_boundary.py`.
