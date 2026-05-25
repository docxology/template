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
2. Identify the failing stage from the `Stage N failed` line.
3. Locate the matching section below by stage number.

---

## Stage 0 — Clean output directories

**Symptom:** `Permission denied` removing files in `output/`.

```text
PermissionError: [Errno 13] Permission denied: 'output/<project>/.../foo.pdf'
```

**Causes & fix**

- A file is held open in another process (Preview, browser, editor). Close it,
  then re-run.
- The file was created by `root` (e.g., from a Docker run on Linux). `sudo
  chown -R "$USER:" output/` then re-run.

---

## Stage 1 — Environment Setup

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

## Stage 2 — Project tests

See [`test-failures.md`](test-failures.md) for the full catalog. Most-common
modes:

- **Coverage gate failed** — bump the missing branches; coverage tables live
  in `output/<project>/htmlcov/index.html`.
- **`ImportPathMismatchError: ('tests.conftest', ...)`** — the
  `ARCH-CONFTEST-1` collision documented in
  [`../../../TO-DO.md`](../../../TO-DO.md). Run one pytest subprocess per
  project; never collect across projects in one process.

---

## Stage 3 — Project Analysis

**Symptom:** Analysis script exits 0 but produces no figure files.

**Check:**

```bash
find projects/<name>/output/figures -type f -newer pyproject.toml
```

If empty, the script is silently failing. Re-run with `LOG_LEVEL=0` to surface
debug output, and confirm the script `print(str(output_path))`-s its outputs
to stdout for the manifest.

**Symptom:** Script timeout (`Per-script timeout: 7200s`).

**Fix:** Either reduce the work, increase `ANALYSIS_SCRIPT_TIMEOUT_SEC` env
var, or split the script into stages.

---

## Stage 4 — Multi-format rendering

> The "PDF Rendering" stage actually emits PDF + HTML + Slides + optional
> DOCX/EPUB. See [`../logging/output-design.md`](../logging/output-design.md)
> for the visual contract.

**Symptom:** `[skip] PDF rendering disabled in config (render.formats.pdf=false)`.

This is the **expected** log line when a format is gated off. Confirm intent
by checking `projects/<name>/manuscript/config.yaml` `render.formats` block.

**Symptom:** `[skip] DOCX rendering: no combined markdown found`.

The DOCX/EPUB renderers reuse the preprocessed `_combined_manuscript.md`
produced by the PDF stage. If PDF rendering is disabled, DOCX/EPUB
cascade-skip. To produce DOCX/EPUB without PDF, set
`render.formats.pdf: true` even if you don't need the PDF artifact.

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

## Stage 5 — Output Validation

**Symptom:** `MARKDOWN.LINK_BAD_TEXT` (non-informative link text).

**Fix:** Replace bare-code link text like `infrastructure/prose/` with
descriptive prose explaining where the link goes.

**Symptom:** Validation reports "no figures found".

**Check:** Confirm the analysis stage ran AND that
`infrastructure/rendering/manuscript_discovery.py::verify_figures_exist`
finds them under `projects/<name>/output/figures/`.

---

## Stage 6 — Copy Outputs

**Symptom:** `Could not copy output/.../pdf/foo.pdf to output/<project>/pdf/`.

**Cause:** the source PDF wasn't produced (Stage 4 partially failed). Re-run
Stage 4 with `LOG_LEVEL=0` to find the underlying renderer error.

---

## LLM stages (optional — only when `--no-llm` is not passed)

**Symptom:** `Failed to connect to Ollama at http://localhost:11434`.

**Fix:** `ollama serve` (in another shell), then `ollama pull gemma3:4b`. The
LLM stages are gated; if you don't want them, run with `--core-only` or
`--no-llm`.

**Symptom:** LLM review times out.

**Fix:** Bump `LLM_TIMEOUT_SEC` env (default 600). Slow CPUs may need 1200+.

---

## CI / GitHub Actions failures

**Symptom:** PR check `lint` fails on `scripts/check_tracked_projects.py`.

You added a non-template project under `projects/` and tried to push.
Per the [private-projects-repo contract](../../maintenance/private-projects-repo.md),
only the public canonical exemplars listed in
[`docs/_generated/active_projects.md`](../../_generated/active_projects.md)
are git-tracked. Move other projects out of
`projects/` and re-push.

**Symptom:** Coverage job `pytest --cov=infrastructure --cov-fail-under=60`
fails.

A new untested module dropped coverage below 60. Either add tests or move
the new code under an explicit `# pragma: no cover` if it's intentionally
diagnostic-only.

---

## General debugging tactics

- Always run with `LOG_LEVEL=0` (DEBUG) to surface the underlying tool
  invocation. Default is `LOG_LEVEL=1` (INFO).
- `LOG_TERMINAL_VERBOSE=1` to restore the verbose `[ts] [LEVEL] msg` prefix
  on the terminal (the file always has it).
- `docs/_generated/last-run-summary.md` shows the most recent end-of-run
  multi-project summary. Diff against a known-good prior run to spot
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
