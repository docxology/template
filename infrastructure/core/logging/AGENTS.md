# infrastructure/core/logging/ - Logging Helper Documentation

## Purpose

The `infrastructure/core/logging/` package contains shared logging setup,
formatting, progress, and diagnostics helpers.

## Files

- `utils.py` - logger helpers and decorators
- `setup.py` - logging setup helpers
- `progress.py` - progress-aware logging
- `pipeline_logging.py` - pipeline log formatting
- `helpers.py` - shared logging helpers
- `formatters.py` - log formatters
- `diagnostic.py` - diagnostic logging helpers (`DiagnosticEvent`,
  `DiagnosticSeverity`, `DiagnosticReporter`)
- `constants.py` - logging constants

## `DiagnosticEvent` schema

`DiagnosticEvent` is the canonical record produced by every validator
that participates in the rendering pipeline. JSON round-trips through
`DiagnosticReporter.save_report` / re-load are stable, so consumers can
persist reports for trend analysis.

| Field            | Type                       | Required | Notes                                                                                  |
|------------------|----------------------------|----------|----------------------------------------------------------------------------------------|
| `severity`       | `DiagnosticSeverity`       | yes      | `ERROR`, `WARNING`, or `INFO`. Promotes warnings to errors in `DiagnosticReporter.has_errors` only when caller opts in. |
| `category`       | `str`                      | yes      | Coarse user-facing grouping (e.g. `MARKDOWN_LINK`).                                     |
| `message`        | `str`                      | yes      | Human-readable description.                                                            |
| `code`           | `str \| None` (default `None`) | no   | Stable, dotted ID (e.g. `MARKDOWN.PANDOC_BARE_PIPE`). See content registry below. **Adding** a code is non-breaking; **changing** an existing one is a breaking change for downstream filters. |
| `file_path`      | `str \| Path \| None`      | no       | Source file the finding is anchored to. Serialised as a string.                         |
| `line_number`    | `int \| None`              | no       | 1-indexed line within `file_path`.                                                     |
| `fix_suggestion` | `str \| None`              | no       | One-line remediation hint shown by `print_report`.                                     |
| `context`        | `dict[str, Any]`           | no       | Arbitrary structured payload (defaults to `{}`).                                       |

`DiagnosticReporter.print_report` prefixes each line with the `code`
when present:

```
  MARKDOWN.PANDOC_BARE_PIPE [MARKDOWN_PANDOC_MID] manuscript/01_intro.md: Bare pipe pattern '|N400|' ...
```

The content-validator code registry lives at
[`infrastructure/validation/content/diagnostic_codes.py`](../../validation/content/diagnostic_codes.py)
(see `MarkdownCode` and `BibtexCode`).

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../../validation/content/AGENTS.md`](../../validation/content/AGENTS.md) — code-registry table
