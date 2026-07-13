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
stdout: JSON object { "exit_code": int, "stdout": string, "stderr": string }
exit:   0 = execution completed (check inner exit_code for code result)
        1 = executor error (malformed input, environment failure)
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
- Do not pass secrets or credentials in the `code` field; use environment variables in the execution context.

## Dependencies

| Dependency | Purpose | Required |
|---|---|---|
| `bash` ≥ 3.2 | Script runtime | Yes |
| `python3` | Default execution language | Recommended |
| `jq` | JSON parsing in scripts | Recommended |
