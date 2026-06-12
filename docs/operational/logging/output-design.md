# Output Design

Logging output has two audiences: the terminal (humans, immediate) and the
log file (grep, audit). They get different formats by design — the terminal
is optimised for at-a-glance readability while the log file is optimised for
post-mortem analysis. This document is the visual contract for what those
two surfaces look like and where the schema is enforced in code.

## Audience split

| Audience | Format | Where | Verbosity dial |
|----------|--------|-------|----------------|
| Human (terminal) | Compact, prefix-less, emoji-friendly | stderr / stdout via the console handler | `LOG_LEVEL`, `NO_EMOJI`, `LOG_TERMINAL_VERBOSE` |
| Grep / audit | Full `[ts] [LEVEL] name: message` | `projects/{name}/output/logs/pipeline.log` | `LOG_LEVEL` only (file format is fixed) |
| Machine / aggregator | Single-line JSON record | stdout when `STRUCTURED_LOGGING=1` | `STRUCTURED_LOGGING` |

The split is intentional: a terminal user wants to see "✅ stage passed in
1m 23s" without a 32-character timestamp prefix on every line, while a
log-file consumer wants the timestamp on every line so `grep`, `awk`, and
diff-across-runs all stay trivial. The two are produced by **different
handlers attached to the same logger** — see "File handler vs console
handler" below.

## Reference: clean run

Canonical clean-run summary — template repo, illustrative multi-project run (project names rotate; counts are not authoritative):

```
================================================================================
                        MULTI-PROJECT EXECUTION SUMMARY
           3 projects  ·  3 succeeded  ·  0 failed  ·  100.0% success
                   wall time 23m 20s  ·  avg/project 7m 46s
================================================================================

PROJECT STATUS
--------------------------------------------------------------------------------
 ✅  <project_a>                      7/7 stages  20m 47s  out: 230.13 MB
 ✅  template_code_project            7/7 stages   1m 32s  out:   6.47 MB
 ✅  template_prose_project           7/7 stages   1m 01s  out:   1.77 MB

STAGE TIMING BREAKDOWN
--------------------------------------------------------------------------------
 Stage                             Avg     Total          Status
 Project Analysis               6m 34s   19m 42s          3/3 ok
 PDF Rendering                  1m 29s    4m 27s          3/3 ok
 Project Tests                    44.0s    2m 12s          3/3 ok
 Environment Setup               10.0s     30.1s          3/3 ok
 Output Validation                0.5s      1.6s          3/3 ok
 Copy Outputs                     0.5s      1.5s          3/3 ok
 Clean Output Directories         0.0s      0.2s          3/3 ok

PERFORMANCE HIGHLIGHTS
--------------------------------------------------------------------------------
  Fastest project: template_prose_project  (1m 01s)
  Slowest project: actinf_policy_entanglement_lean  (20m 47s)
OUTPUT LOCATIONS
--------------------------------------------------------------------------------
  Output PDF     : output/actinf_policy_entanglement_lean/actinf_policy_entanglement_lean_combined.pdf
  Output PDF     : output/template_code_project/template_code_project_combined.pdf
  Output PDF     : output/template_prose_project/template_prose_project_combined.pdf

NEXT STEPS
--------------------------------------------------------------------------------
  • All projects passed. Inspect outputs under output/<project>/

================================================================================
                      🎉 ALL 4 PROJECTS PASSED  ·  67m 21s
================================================================================
```

This block is the canonical end-of-run summary. It is rendered by
`format_multi_project_detailed_report` in
[`infrastructure/reporting/multi_project_report.py`](../../../infrastructure/reporting/multi_project_report.py)
(re-exported from
[`infrastructure/core/pipeline/multi_project.py`](../../../infrastructure/core/pipeline/multi_project.py)),
emitted by the orchestrator in
[`infrastructure/orchestration/pipeline_runner.py`](../../../infrastructure/orchestration/pipeline_runner.py),
and persisted verbatim to `docs/_generated/last-run-summary.md` after every
multi-project run.

## Reference: per-project stages

Per-project trace from one successful project in the same run. The leading
icon, stage number, name, and duration line up vertically so a stack of
projects in a multi-project run remains visually scannable.

```
[0/9] Clean Output Directories      ✅  0.0s
[1/9] Environment Setup             ✅  9.8s
[2/9] Infrastructure Tests          ⏭   skipped (multi-project mode)
[3/9] Project Tests                 ✅  2m 41s
[4/9] Project Analysis              ✅  10m 14s
[5/9] PDF Rendering                 ✅  3m 02s
[6/9] Output Validation             ✅  0.6s
[7/9] LLM Scientific Review         ⏭   skipped (--core-only)
[8/9] LLM Translations              ⏭   skipped (--core-only)
[9/9] Copy Outputs                  ✅  0.5s
```

Within the render stage, `log_rendering_summary` in
[`infrastructure/rendering/_pipeline_summary.py`](../../../infrastructure/rendering/_pipeline_summary.py)
emits a per-project block of its own — combined PDF size, individual section
PDFs, web outputs, slides, and total output size — wrapped in
`RENDERING RESULTS SUMMARY` separator bars.

## Failure mode reference

A failed run keeps the same overall shape; only the deltas matter:

- The banner shows `N/M succeeded · failed · success-rate%` with `failed > 0`.
- The failing project's row in `PROJECT STATUS` swaps `✅` for `❌` and gets
  a `   failed at: <stage>` suffix naming the first non-`success` stage.
- A new `FAILURE DETAILS` section appears **between** `PERFORMANCE
  HIGHLIGHTS` and `OUTPUT LOCATIONS`. For each failed project it prints:
  - `❌ <project_qualified_name>`
  - `   Stage : <stage_name>`
  - `   Error : <first 159 chars of error_message>` (if present)
  - `   Log   : projects/<name>/output/logs/pipeline.log` (if it exists)
  - `   Report: projects/<name>/output/reports/test_results.md` (if it exists)
- The closing banner swaps the `🎉 ALL N PASSED` line for
  `⚠️  S/N succeeded · F failed · <wall-time>`.
- `NEXT STEPS` swaps the inspect-outputs hint for two pointers:
  - `Re-run a failed project: ./run.sh --project <name> --pipeline --core-only --skip-infra`
  - `Inspect a failure log : cat projects/<name>/output/logs/pipeline.log`

The presence of the literal strings `FAILURE DETAILS`,
`PERFORMANCE HIGHLIGHTS`, `OUTPUT LOCATIONS`, `NEXT STEPS`,
`MULTI-PROJECT EXECUTION SUMMARY`, `PROJECT STATUS`, and
`STAGE TIMING BREAKDOWN` is part of the function's stability contract —
tests in `tests/infra_tests/core/test_multi_project_detailed_report.py`
assert on these substrings and they must not change without a coordinated
update.

## Summary block schema

The multi-project summary, top to bottom:

- **Banner** — three centered lines inside `=` bars: title
  (`MULTI-PROJECT EXECUTION SUMMARY`), aggregate counts
  (`N projects · S succeeded · F failed · X.X% success`), and timing
  (`wall time <total> · avg/project <avg>`). If infrastructure tests ran
  separately at the top of the run, a fourth centered line shows that
  duration.
- **PROJECT STATUS** — per-project row of `<icon> <name> <ok>/<total>
  stages <duration> out: <size>`, with an optional `   failed at: <stage>`
  suffix for failures. Rows preserve the orchestrator's discovery order so
  the reader can correlate against the project-by-project trace above.
- **STAGE TIMING BREAKDOWN** — one row per distinct stage name observed
  across all projects, with `Avg`, `Total`, and `N/N ok` columns. Rows are
  **sorted by total duration descending** so the most expensive stage is
  always at the top.
- **PERFORMANCE HIGHLIGHTS** — fastest and slowest project by total
  duration, with their wall-time in parens. Useful as a single-line
  regression signal between runs.
- **FAILURE DETAILS** *(only if any project failed)* — one block per failed
  project naming the first failing stage, the truncated error, and pointers
  to the project's log file and test-results report.
- **OUTPUT LOCATIONS** — repo-relative paths to the multi-project summary
  Markdown report (if generated) and to each succeeded project's combined
  PDF (first two PDFs per project).
- **NEXT STEPS** — one bullet on success (inspect outputs), or two bullets
  on failure (re-run command + log path).
- **Closing banner** — `🎉 ALL N PROJECTS PASSED · <wall>` on full success
  or `⚠️  S/N succeeded · F failed · <wall>` otherwise, framed by `=` bars.

## Verbosity dial

| Variable | Values | What it changes |
|----------|--------|-----------------|
| `LOG_LEVEL` | `0`, `1`, `2`, `3` | `0=DEBUG`, `1=INFO` (default), `2=WARN`, `3=ERROR` — filters both handlers |
| `NO_EMOJI` | `1` / `true` | Strips emoji from console output; file output is unaffected |
| `STRUCTURED_LOGGING` | `1` / `true` | Switches console handler to single-line JSON for log aggregators |
| `LOG_TERMINAL_VERBOSE` | `1` / `true` | Restores the full `[ts] [LEVEL] name:` prefix on the console handler (matches the file format) |

`LOG_TERMINAL_VERBOSE` is the escape hatch when a terminal user needs the
same line shape as the log file — for example, when piping terminal output
into a diff against `pipeline.log` to confirm the two handlers agree on a
specific event.

## File handler vs console handler

Every PAI/template logger is wired with two handlers:

1. **File handler** writes to `projects/{name}/output/logs/pipeline.log`
   (and, in a few orchestration paths, to the global run log). It always
   uses the full `[YYYY-MM-DDTHH:MM:SSZ] [LEVEL] logger.name: message`
   format. This format is **fixed** — downstream `grep` and `awk` pipelines
   depend on it. Verbosity is filtered by `LOG_LEVEL`; everything else
   passes through.
2. **Console handler** writes to stderr (or stdout for `STRUCTURED_LOGGING`)
   and uses the compact prefix-less format by default. `NO_EMOJI` strips
   icons; `LOG_TERMINAL_VERBOSE` restores the long-form prefix;
   `STRUCTURED_LOGGING` swaps the whole format for JSON.

Because both handlers attach to the same logger, a single
`logger.info("…")` call always lands in both places — there is no "log to
file only" / "log to terminal only" mode by design.

## See also

- [README.md](README.md) — logging guide index and quick start
- [python-logging.md](python-logging.md) — Python logger API and config
- [bash-logging.md](bash-logging.md) — shell-script logging helpers
- [logging-patterns.md](logging-patterns.md) — cross-language patterns
- [../reporting-guide.md](../reporting-guide.md) — full reporting system,
  including the JSON/HTML/Markdown reports written alongside the
  end-of-run summary block
