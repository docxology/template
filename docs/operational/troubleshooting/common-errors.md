# Common Errors

> Catalog of frequent failure modes by pipeline stage, with actionable
> remediation. Linked from
> [`README.md`](README.md) and from `build-tools.md`.
>
> _Companion to [`recovery-procedures.md`](recovery-procedures.md) (broader
> rollback procedures) and [`test-failures.md`](test-failures.md)
> (test-suite-specific failures)._

## Quick triage

1. Read the pipeline log: `tail -200 projects/<name>/output/logs/pipeline.log`
2. Identify the stable stage key/name and the script path from the failure.
3. Locate the matching section below. Script prefixes and display numbers are
   not stable identifiers: optional stages change the displayed position.

---

## `clean` — Clean Output Directories

**Symptom:** `Permission denied` removing files in `output/`.

```text
PermissionError: [Errno 13] Permission denied: 'output/<project>/.../foo.pdf'
```

**Causes & fix**

- A file is held open in another process (Preview, browser, editor). Close it,
  then re-run.
- The file was created by another user (for example, a root-owned Docker
  output). Inspect exact ownership first. Changing ownership recursively is a
  privileged, potentially broad mutation; limit any authorized correction to
  the selected project's generated output tree.

---

## `setup` — Environment Setup

**Symptom:** `uv: command not found` or `uv sync` fails.

**Fix:** Install `uv` per the official guide at <https://docs.astral.sh/uv/>.
Two common paths: `pip install uv`, or follow the published shell installer
on the uv docs page. Then run `uv sync` from the repo root.

**Symptom:** `pandoc: command not found` when rendering HTML / DOCX / EPUB.

**Fix:** `brew install pandoc` (macOS) or
`apt-get install pandoc` (Debian). DOCX and EPUB require pandoc >= 2.10.

**Symptom:** `xelatex: command not found` when building combined PDF.

**Fix:** Install BasicTeX / TeX Live; then `sudo tlmgr install multirow
cleveref doi newunicodechar`.

---

## `infra_tests` / `project_tests` — Tests

See [`test-failures.md`](test-failures.md) for the full catalog. Most-common
modes:

- **Coverage gate failed** — add meaningful behavior and failure-path coverage;
  do not exempt code or weaken the floor merely to clear the percentage.
- **`ImportPathMismatchError: ('tests.conftest', ...)`** — the
  `ARCH-CONFTEST-1` collision documented in
  [`../../../TO-DO.md`](../../../TO-DO.md). Run one pytest subprocess per
  project; never collect across projects in one process.

---

## `analysis` — Project Analysis

**Symptom:** Analysis script exits 0 but produces no figure files.

**Check:**

```bash
find projects/<name>/output/figures -type f -newer pyproject.toml
```

If empty, determine whether the producer failed, intentionally emitted no
artifact, or wrote elsewhere. Re-run with `LOG_LEVEL=0`, inspect the declared
artifact contract, and confirm the script reports produced paths. Do not infer
silent failure from an empty timestamp query alone.

**Symptom:** Script timeout (`Per-script timeout: 7200s`).

**Fix:** Either reduce the work, increase `ANALYSIS_SCRIPT_TIMEOUT_SEC` env
var, or split the script into stages.

---

## `render_pdf` — Manuscript hydration and multi-format rendering

> The "PDF Rendering" stage actually emits PDF + HTML + Slides + optional
> DOCX/EPUB. See [`../logging/output-design.md`](../logging/output-design.md)
> for the visual contract.

**Symptom:** `[skip] PDF rendering disabled in config (render.formats.pdf=false)`.

This is the **expected** log line when a format is gated off. Confirm intent
by checking `projects/<name>/manuscript/config.yaml` `render.formats` block.

**Symptom:** `[skip] DOCX rendering: no combined markdown found`.

The default Stage 3 path now builds a fresh shared
`output/web/_combined_manuscript.md` from the current ordered manuscript inputs
whenever DOCX or EPUB is enabled; it does not require PDF. This skip message
therefore indicates a direct or legacy renderer call that did not supply a
current combined source, or a failed combined-source preparation step. Run the
normal Stage 3 command, confirm current manuscript files were discovered, and
inspect `output/reports/manuscript_composition.json`. Do not enable PDF merely
to work around this message.

**Symptom:** `pandoc DOCX render failed (exit 1)`.

```text
pandoc DOCX render failed (exit 1): ...could not parse reference doc...
```

**Causes & fix**

- The `--reference-doc=` path is wrong. Confirm with
  `ls -la <reference_doc_path>`.
- Pandoc < 2.10. Upgrade.

**Symptom:** `LaTeX compilation completed in 2.56s` but the PDF is 0 bytes or
absent.

Tail the per-section `output/<project>/slides/<section>_slides.log` or
`output/<project>/pdf/_xelatex_stdout.log` for the actual TeX error. Often a
missing package — install with `tlmgr install <package>`.

**Symptom:** `Spinner garble — ⠋ Running project tests... mid-line with PASSED`.

Fixed in this repo by `TestSuiteConfig.streaming_subprocess: bool = True` at
pytest call sites. If you wrote a new test-runner wrapper, set
`streaming_subprocess=True` to suppress the spinner — see
[`test-failures.md`](test-failures.md).

---

## `validate` — Output Validation (`stage_04_validate.py`)

**Symptom:** `MARKDOWN.LINK_BAD_TEXT` (non-informative link text).

**Fix:** Replace bare-code link text like `infrastructure/prose/` with
descriptive prose explaining where the link goes.

**Symptom:** Validation reports "no figures found".

**Check:** Confirm the analysis stage ran AND that
`infrastructure/rendering/manuscript_discovery.py::verify_figures_exist`
finds them under `projects/<name>/output/figures/`.

---

## `copy` — Copy Outputs (`stage_05_copy.py`)

**Symptom:** `Could not copy output/.../pdf/foo.pdf to output/<project>/pdf/`.

**Cause:** the source PDF was not produced or the source/destination project
identity disagrees. Re-run the `render_pdf` producer
(`stage_03_render.py --project <qualified-name>`) with `LOG_LEVEL=0`, then
validate before copying.

---

## `llm_reviews` / `llm_translations` (optional)

**Symptom:** `Failed to connect to Ollama at http://localhost:11434`.

**Fix:** `ollama serve` (in another shell), then `ollama pull gemma3:4b`. The
LLM stages are gated; if you don't want them, run `execute_pipeline.py` with
`--core-only` or `--skip-llm` (the multi-project orchestrator
`execute_multi_project.py` uses `--no-llm`). Record the omitted LLM lanes as
`not run`, not passed.

**Symptom:** LLM review times out.

**Fix:** Bump `LLM_REVIEW_TIMEOUT` env (default 300; the per-request
`LLM_TIMEOUT` default is 60). Slow CPUs may need 600+.

---

## CI / GitHub Actions failures

**Symptom:** PR check `lint` fails on the step "Confidentiality guard — only
public template resources tracked" (`scripts/audit/check_tracked_all.py`).

You added a non-template resource under one of the four guarded pools —
`projects/`, `fonds/`, `rules/`, or `tools/` — and tried to push.
Per the [private-projects-repo contract](../../maintenance/private-projects-repo.md),
only each pool's `templates/` subtree is git-tracked; for `projects/` that is
the public canonical exemplars listed in
[`docs/_generated/active_projects.md`](../../_generated/active_projects.md).
Preserve the files, remove them from the public index or relocate them to the
configured external sidecar as appropriate, then re-run all four-pool and
generated-artifact guards before any push. Do not delete unrelated local work.

**Symptom:** Coverage job `pytest --cov=infrastructure --cov-fail-under=60`
fails.

A new or changed path dropped measured coverage below 60%. Add meaningful tests
or redesign unreachable/dead code. A coverage exclusion requires an explicit,
reviewed policy justification; it is not routine remediation for a failing
gate.

---

## General debugging tactics

- Always run with `LOG_LEVEL=0` (DEBUG) to surface the underlying tool
  invocation. Default is `LOG_LEVEL=1` (INFO).
- `LOG_TERMINAL_VERBOSE=1` to restore the verbose `[ts] [LEVEL] msg` prefix
  on the terminal (the file always has it).
- `docs/_generated/last-run-summary.md` shows the last recorded end-of-run
  multi-project summary; it is historical evidence, not a current health claim.
  Diff it against a known-good prior run to spot
  regressions.
- `docs/operational/logging/output-design.md` is the visual-contract
  reference for what each stage should look like.

---

## Still stuck?

1. File an issue with the failing stage label, the project name, the
   relevant `pipeline.log` excerpt, and the exact command line.
2. Or, run `uv run python -m infrastructure.doctor` for a guided diagnosis.

## See also

- [`recovery-procedures.md`](recovery-procedures.md) — broader rollback procedures
- [`test-failures.md`](test-failures.md) — pytest-specific failures
- [`build-tools.md`](build-tools.md) — tool-chain (xelatex, pandoc, mermaid) issues
- [`../logging/output-design.md`](../logging/output-design.md) — visual contract for pipeline output
