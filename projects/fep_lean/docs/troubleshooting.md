# Troubleshooting — fep_lean

**Version**: v0.7.0 | **Status**: Active | **Last Updated**: April 2026

Ground-truthed against a live end-to-end run (2026-04-09). If you hit an issue not listed here, open one against [this repo](../../README.md) with the exact command, the offending log snippet, and the output of `uv run fep-lean-preflight`.

---

## Quick diagnostic

Run these from the **`fep_lean` project root** (`projects/fep_lean/` in the monorepo) — they resolve most issues:

```bash
cd projects/fep_lean   # or: cd <path-to>/fep_lean

uv sync --extra dev
uv run fep-lean-preflight
uv run pytest tests/ -q --timeout=900 --cov=src --cov-fail-under=89
```

From the monorepo root without `cd`, equivalent: `uv run --directory projects/fep_lean fep-lean-preflight` and `uv run --directory projects/fep_lean pytest tests/ ...`.

Expected good state: preflight exits 0, `uv sync` installs without errors, test suite reports **320** collected / all green (`uv run pytest tests/ --collect-only -q`) with **≥90%** line coverage on `src/` (run pytest from this directory so `[tool.coverage.run] source = ["src"]` applies).

---

## Catalogue figures (`ProcessPoolExecutor`) or coverage surprises

**Symptoms**: errors from `multiprocessing` / `concurrent.futures` spawn workers when generating the nine PNGs under `output/figures/`, or coverage totals look **low** when pytest was launched from the monorepo root with a mismatched `--cov=` prefix.

**Mitigations**:

```bash
export FEP_LEAN_FIGURES_MP=0   # force in-process serial matplotlib (same outputs)
```

See [pipeline.md](pipeline.md) (parallelism) and [configuration.md](configuration.md#pipeline-orchestration) (`FEP_LEAN_FIGURES_MP`). For coverage, run `uv run pytest tests/ --cov=src` from **`projects/fep_lean/`** so `pyproject.toml` paths and `concurrency = ["multiprocessing"]` match `pytest-cov`.

---

## Hermes / OpenRouter: `IncompleteRead`, 429, and dropped streams

**Symptoms**: log lines mentioning `http.client.IncompleteRead`, `Connection reset`, or Hermes warnings about **transient network** / **429 rate limit** during `GaussRunner` / `01_fep_catalogue_and_figures.py`.

**Cause**: OpenRouter (or intermediaries) may use chunked transfer; a dropped connection mid-body surfaces as `IncompleteRead` in Python’s stdlib HTTP client. Rate limits return HTTP **429**.

**What the code does** ([`src/llm/hermes.py`](../src/llm/hermes.py)): `_call_api` maps transport failures to `HermesAPIError` with **`transient=True`**; `_try_fetch_raw` retries **429** and **transient** errors on the **same** model with exponential backoff, bounded by **`HERMES_429_MAX_RETRIES`** and **`HERMES_NETWORK_MAX_RETRIES`** (defaults **2** each). See [hermes.md](hermes.md#http-transport-hermesapierror-and-retries).

**If failures persist**: increase backoff budgets (`HERMES_NETWORK_MAX_RETRIES`, `HERMES_429_MAX_RETRIES`), check WAN stability, or switch `hermes.model` / fallbacks in `config/settings.yaml`. Hermes is not disabled for transport-only errors (`status_code is None`).

---

## Lean4-skills `/lean4:doctor` vs this repo

The **lean4-skills** plugin’s `/lean4:doctor` command checks elan, `LEAN4_SCRIPTS`, optional Lean LSP MCP tools, and legacy-plugin migration paths (see plugin docs). **`fep_lean` does not bundle that plugin**; use it in the editor when you need Mathlib search / goal inspection.

**Rough mapping** when something is wrong with Lean in *this* project:

| Symptom | In-repo step |
| --------|-------------- |
| `lean` / `lake` missing | **§4** below (elan + PATH) |
| Mathlib `.olean` missing | **§5** (`cd lean && lake exe cache get && lake build`) |
| Stale `_verify_*` breaking `lake build` | **§6** |
| Full toolchain probe | `uv run fep-lean-preflight` (see [README.md](../README.md), [configuration.md](configuration.md)) |

Editor workflows for catalogue work are summarized in [lean4.md](lean4.md). For SSOT and regeneration, see [authorship-guide.md](authorship-guide.md).

---

## 1. `ModuleNotFoundError: No module named 'infrastructure'`

**When you see it**: running `scripts/01_fep_catalogue_and_figures.py` or another fep_lean script directly with `python3 …`.

**Root cause**: the script imports `infrastructure.core.logging.utils` from the monorepo root. Your Python process doesn't have the repo root on `sys.path`.

**Fix** (any one of):

```bash
# Recommended: from repository root, put the repo and this project's src on PYTHONPATH
# (replace <path-to-fep_lean> with the directory containing this project's pyproject.toml)
export PYTHONPATH=".:<path-to-fep_lean>/src"
uv run python <path-to-fep_lean>/scripts/01_fep_catalogue_and_figures.py

# Or go through the template-level entry point (from repository root)
uv run python scripts/execute_pipeline.py --project fep_lean --core-only --skip-infra
```

---

## 2. `ModuleNotFoundError: No module named 'pipeline'` / `catalogue` / `llm`

**When you see it**: same scripts, different import line.

**Root cause**: This project’s `src/` is not on `sys.path`. The subpackages (`pipeline`, `catalogue`, `llm`, `verification`, `output`, `gauss`) live under `src/`, declared in `pyproject.toml` as `where = ["src"]` and in `pyproject.toml [tool.pytest.ini_options] pythonpath = ["src"]`.

**Fix**:

```bash
# From repository root — export once, or prefix a single command (adjust path to project root)
export PYTHONPATH=".:<path-to-fep_lean>/src"

# Or use uv run from the project root (the pytest pythonpath cfg handles it)
uv run pytest tests/
```

---

## 3. `ModuleNotFoundError: No module named 'matplotlib'`

**When you see it**: running scripts directly with the system `python3` (not the `.venv`).

**Root cause**: the system Python is missing `matplotlib` / `numpy` / `pyyaml`. The project declares them as dependencies in `pyproject.toml:10-14`.

**Fix**:

```bash
# from project root
uv sync --extra dev   # installs numpy, matplotlib, pyyaml, pytest, pytest-cov, pytest-timeout
uv run python scripts/01_fep_catalogue_and_figures.py   # now works
```

If you must use a non-uv interpreter, install manually: `pip install numpy matplotlib pyyaml`.

---

## 4. `lake: command not found` / `lean: command not found`

**When you see it**: preflight fails, or tests under `tests/test_lean_verifier.py` print skip reasons.

**Root cause**: [elan](https://github.com/leanprover/elan) (the Lean toolchain manager) isn't installed or isn't on `PATH`.

**Fix**:

```bash
# Install elan (asks once; installs lake+lean into ~/.elan/bin)
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# Add elan to PATH (bash/zsh)
source $HOME/.elan/env
# …or add '. "$HOME/.elan/env"' to ~/.zshrc / ~/.bashrc

# Verify
lake --version
lean --version   # should match `lean/lean-toolchain` (e.g. Lean (version 4.29.0, ...))
```

**Alternative**: set `FEP_LEAN_LAKE_EXE` and `FEP_LEAN_LEAN_EXE` to the absolute paths of a pre-installed toolchain, bypassing `PATH` entirely:

```bash
export FEP_LEAN_LAKE_EXE=/opt/homebrew/bin/lake
export FEP_LEAN_LEAN_EXE=/opt/homebrew/bin/lean
```

---

## 5. `Mathlib not built` (preflight fails on `mathlib_built` check)

**When you see it**: preflight reports `[FAIL] mathlib_built: .lake/build/lib/Mathlib.olean not found`.

**Root cause**: The `FepSketches` Lake workspace hasn't fetched the prebuilt Mathlib cache yet, or you ran `lake clean` and removed the compiled `.olean` files.

**Fix**:

```bash
cd lean
lake exe cache get     # ~3 GB download; fetches prebuilt Mathlib olean artifacts
lake build             # ensures FepSketches itself compiles
```

This is a one-time ~5-minute operation. Once the cache is populated, subsequent runs are fast.

---

## 6. `lake build` fails with `_verify_fep-NNN_<hash>` error

**When you see it**: running `cd lean && lake build` from the project root and it errors on a stale file that isn't actually in the workspace.

**Root cause**: `LeanVerifier` writes temporary `_verify_*.lean` files into `lean/FepSketches/` to resolve Mathlib imports, then deletes them after `lake env lean` finishes. Lake caches the resulting `.olean` under `.lake/build/lib/FepSketches/`, and if a prior process crashed before the cleanup finally-block ran (`src/verification/lean_verifier.py` temp-file lifecycle), you can end up with a stale `.olean` whose source was deleted. `lake build` (which walks the filesystem + manifest) then refuses to rebuild a phantom module.

**Fix**:

```bash
# From project root — clean the orphan temp sources (if any remain)
find lean/FepSketches -maxdepth 1 -name "_verify_*.lean" -delete

# Clean the stale build artifacts
find lean/.lake/build/lib/FepSketches -name "_verify_*" -delete
find lean/.lake/build/ir/FepSketches -name "_verify_*" -delete

# Re-run lake build — should succeed in seconds (Mathlib cache is intact)
cd lean && lake build
```

> **Note**: The test suite itself does **not** use `lake build`; it uses `lake env lean <tmpfile>` on individual files and is unaffected by this hygiene issue.

---

## 7. Hermes stage skipped with "no API key"

**When you see it**: pipeline runs but `hermes_report.md` shows `❌` for all topics and the log says `no API key (set OPENROUTER_API_KEY or ANTHROPIC_API_KEY)`.

**Root cause**: Hermes has no API key to authenticate with OpenRouter (primary) or Anthropic (fallback). This is **not** an error — it's intentional graceful degradation, the thin pipeline runs fine without it.

**Fix** (only if you actually want live LLM calls):

```bash
# Option A: export in the shell
export OPENROUTER_API_KEY=sk-or-v1-...
# or:
export ANTHROPIC_API_KEY=sk-ant-v3-...

# Option B: write to ~/.gauss/.env (auto-loaded by OpenGaussClient)
mkdir -p ~/.gauss
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> ~/.gauss/.env

# Enable workflows
export FEP_LEAN_GAUSS_WORKFLOWS=1

# Run (from project root)
uv run python scripts/01_fep_catalogue_and_figures.py
```

**Key↔endpoint validation**: if your `OPENROUTER_API_KEY` starts with `sk-ant-`, Hermes will disable itself with an error log. Use keys matching the configured `HERMES_API_BASE` (`sk-or-*` for OpenRouter, `sk-ant-*` for Anthropic). See `hermes.md` ‘Key ↔ Endpoint Affinity Validation’.

---

## 7b. Hermes request never returns / pipeline hangs at one topic for >5 minutes {#hermes-wall-clock}

**When you see it**: a Hermes call appears to complete the network handshake (TCP `ESTABLISHED` to `104.18.*` / OpenRouter) but the pipeline log goes silent for several minutes on a single topic. Earlier observations on `z-ai/glm-5.1` saw 10+ minute waits with `content: ""`.

**Root cause**: `urllib.request.urlopen(..., timeout=N)` only bounds **individual** socket operations (connect, each `recv`). A reasoning model that streams a few bytes every few seconds keeps each socket op under the timeout indefinitely. `HermesConfig.timeout_s` (default 150 s) was therefore not a true wall-clock budget on streaming models.

**Fix already in tree**: `_make_request` in [`src/llm/hermes.py`](../src/llm/hermes.py) runs the blocking `urlopen + read` inside a worker thread and `join`s with `timeout=timeout`. If the worker is still alive at the deadline, it raises a transient `HermesAPIError("Wall-clock timeout after Ns …")` and the chain advances to the next model. Reasoning models (`Kimi K2.x`, `GLM-5.1`, `DeepSeek-R1`, `o1/o3`, `Nemotron-3-super`) are listed in `_REASONING_MODELS` so they get `reasoning_max_tokens` (65 536) and `reasoning_timeout_s` (300 s) instead of the instruct budgets.

**If you still see hangs**:

1. Check `pipeline.log` for `Wall-clock timeout after Ns` lines — they show which model exhausted the budget.
2. Lower `HERMES_REASONING_TIMEOUT_S` for tighter feedback if you suspect a single bad model is blocking the chain.
3. Confirm the key is OpenRouter (`sk-or-*`) and the endpoint is `https://openrouter.ai/api/v1`.

---

## 8. Hermes HTTP 401 / 403 from OpenRouter {#hermes-http-403}

**When you see it**: either at preflight (0 s) or on the first topic:

```text
Hermes API error (model=moonshotai/kimi-k2.6, topic=fep-001):
  HTTP 403: Forbidden — {"error":{"message":"Key limit exceeded (total limit). …"}}
Disabling Hermes for remainder of run (HTTP 403 at topic=fep-001, …).
  Manage the OpenRouter key at https://openrouter.ai/settings/keys, or set
  HERMES_API_BASE=https://api.anthropic.com/v1 with ANTHROPIC_API_KEY …
```

**Root cause** (two variants):

- **401 Unauthorized**: invalid or revoked key.
- **403 "Key limit exceeded"**: the OpenRouter account itself has hit a
  credit or request cap (not a per-model 429).

Either way, `HermesExplainer` flips `HermesConfig.enabled=False` once and
the rest of the run continues **Lean-only** (topics still compile; the
manuscript section for each topic gets an empty Hermes explanation).

**Preflight**: as of `hermes.py`’s `preflight()` method, the pipeline makes
one `max_tokens=1` probe before the topic batch. A 403 at preflight fails
fast in <10 s instead of wasting ~12 min on Stage 4.

**Fixes** (in priority order):

1. **Rotate or top up the key** at https://openrouter.ai/settings/keys,
   update `~/.gauss/.env` (or the shell export), and re-run.
2. **Switch to Anthropic-direct**:

   ```bash
   export HERMES_API_BASE=https://api.anthropic.com/v1
   export ANTHROPIC_API_KEY=sk-ant-...
   export HERMES_MODEL=claude-sonnet-4-5-20250929
   ./run.sh
   ```

3. **Configure fallback models** that still have quota:

   ```yaml
   # config/settings.yaml
   hermes:
     model: "moonshotai/kimi-k2.6"
     fallback_models:
       - "moonshotai/kimi-k2-thinking"
       - "openai/gpt-oss-120b:free"
       - "qwen/qwen3-next-80b-a3b-instruct:free"
   ```

4. **Run Lean-only** if the manuscript can wait:

   ```bash
   unset OPENROUTER_API_KEY ANTHROPIC_API_KEY
   ./run.sh        # stages 1-3 + figures + catalogue, no LLM
   ```

Cross-refs: [`docs/configuration.md` § User-supplied fallback chain](configuration.md#user-supplied-fallback-chain), [`docs/hermes.md`](hermes.md) (Error Handling table).

---

## 9. Hermes HTTP 429 rate-limited, slow runs

**When you see it**: runs take 30-60 min for 50 topics, with repeated `HTTP 429` lines.

**Root cause**: OpenRouter's free tier has strict per-minute limits on the 120B/405B models. The fallback chain in `hermes.py` tries 6 models on 429; if all are limited, topics are skipped one at a time.

**Fixes**:

- Add a paid model as primary: set `HERMES_MODEL=anthropic/claude-sonnet-4` in `~/.gauss/.env` (also set `ANTHROPIC_API_KEY`). See `configuration.md` ‘Premium / manual overrides’.
- Increase retry budgets (`HERMES_429_MAX_RETRIES`, `HERMES_NETWORK_MAX_RETRIES`) or cap load with `FEP_LEAN_MAX_TOPICS` on free tier. (A `gauss.throttle` block is not in the shipped `settings.yaml` and is not read by the current pipeline; see the `[gauss.throttle]` note in [configuration.md](configuration.md).)
- Run a subset with `uv run python scripts/02_run_single_topic.py --topic fep-001` to test.
- Run the thin pipeline (`FEP_LEAN_GAUSS_WORKFLOWS=0`) — skips Hermes entirely and still generates figures, catalogue, reports, manuscript vars.

---

## 10. Test suite fails on `test_hermes_config_from_settings`

**When you see it**: Specifically `AssertionError: assert 'nvidia/nemot...20b-a12b:free' == 'test-model'`.

**Root cause** (resolved in-tree as of 2026-04-09): the test used `monkeypatch.setenv("GAUSS_HOME", tmp_path)` but the global `HERMES_MODEL` env var was leaking in. If it resurfaces:

**Fix**: ensure the test explicitly `monkeypatch.delenv("HERMES_MODEL", raising=False)` before constructing the config. Grep `test_hermes_explainer.py:44` — the delenv line should be present. If your shell exports `HERMES_MODEL=…`, unset it for the test run.

---

## 11. `lake env lean` segfaults / hangs on macOS

**When you see it**: `LeanVerifier.verify_sketch` times out at 300s for every topic on macOS, subsequent processes spin.

**Root cause**: macOS Sandbox + elan proxy contention. `LeanVerifier` runs with `max_workers=1` precisely to avoid this (see `src/verification/lean_verifier.py`). If you still see hangs, it's usually because `ELAN_HOME` points at a non-writable directory.

**Fix**: `LeanVerifier._subprocess_env()` creates a per-call writable `ELAN_HOME` under `/tmp/`. If that's not working, set one yourself:

```bash
export ELAN_HOME=/tmp/elan-$USER
mkdir -p "$ELAN_HOME"
```

Never run multiple `lake env lean` processes concurrently against the same workspace on macOS.

---

## 12. Pipeline fails at Stage 3 (Infrastructure Tests) — 4 failures

**When you see it**: `uv run python scripts/execute_pipeline.py --project fep_lean --core-only` exits with:

```
✗ Stage 3 failed (Infrastructure Tests)
4 failed, 6035 passed, 13 skipped
FAILED tests/infra_tests/llm/test_llm_core_coverage.py::TestLLMClientQueryIntegration::test_query_basic
FAILED tests/infra_tests/skills/test_skill_discovery.py::TestTemplateRepository::test_manifest_matches_live_discovery
FAILED tests/infra_tests/skills/test_skill_discovery.py::TestCliModule::test_check_exit_zero
FAILED tests/infra_tests/skills/test_skill_discovery.py::TestCliModule::test_subprocess_module_invocation
```

**Root cause**: These are **pre-existing monorepo-wide infrastructure test failures outside fep_lean's scope**. They concern Ollama/LLM tests and the `infrastructure/skills` discovery module. fep_lean's own tests pass cleanly.

**Workaround**: add `--skip-infra`:

```bash
uv run python scripts/execute_pipeline.py --project fep_lean --core-only --skip-infra
```

This runs Stage 2 (Setup) → Stage 3 (Project Tests) → Stage 4 (Analysis) → Stage 5 (PDF) → Stage 6 (Validate) → Stage 7 (Copy). Full end-to-end run takes ~578 s on a 2024 Mac.

---

## 13. `manuscript/09z_appendix_b_lean_catalogue.md` not updating

**When you see it**: You edited `config/topics.yaml` and the appendix still shows old content.

**Root cause**: The appendix is **auto-generated** on every pipeline run from `src/output/manuscript.py::write_full_topic_lean_catalogue_markdown`. It's in `.gitignore` so you can never commit it directly.

**Fix**:

```bash
# from project root
FEP_LEAN_GAUSS_WORKFLOWS=0 uv run python scripts/01_fep_catalogue_and_figures.py
# The appendix is rewritten; re-render the PDF (from repository root):
uv run python scripts/03_render_pdf.py --project fep_lean
```

---

## 14. PDF build hangs or fails silently

**When you see it**: Stage 5 (PDF Rendering) never logs completion.

**Root cause**: Missing LaTeX packages. The template pipeline uses `xelatex` via `pandoc`; some TeX Live distributions ship without `multirow`, `cleveref`, `doi`, `newunicodechar`.

**Fix**:

```bash
# Verify with the infra validator
uv run python -m infrastructure.rendering.latex_package_validator

# Install any missing packages via tlmgr (requires admin):
sudo tlmgr install multirow cleveref doi newunicodechar biblatex

# Re-run just the render stage
uv run python scripts/03_render_pdf.py --project fep_lean
```

For Homebrew MacTeX: `brew install --cask mactex-no-gui` and restart your shell to pick up `tlmgr`.

---

## 15. `FileNotFoundError: output/reports/latest/summary.json`

**When you see it**: Reading code or a script references `output/reports/latest` and it doesn't exist.

**Root cause**: `latest` is a **symlink** created by `Reporter.generate` after a successful run. If no pipeline has run in this project copy, the symlink doesn't exist.

**Fix**:

```bash
# from project root
FEP_LEAN_GAUSS_WORKFLOWS=0 uv run python scripts/04_generate_reports.py
# Now: ls -la output/reports/latest  →  symlink exists
```

---

## Stage 02 subprocess timeout (`Execute … timed out after 7200.0s`)

**When you see it**: the template **Project Analysis** stage fails while running `01_fep_catalogue_and_figures.py` (or another analysis script under this project’s `scripts/`). The repo-root orchestrator [`scripts/02_run_analysis.py`](../../../scripts/02_run_analysis.py) wraps each script in `subprocess.run` with a default timeout of **7200 seconds** (2 hours) per script, from [`infrastructure/core/analysis_timeout.py`](../../../infrastructure/core/analysis_timeout.py).

**Root cause**: full **Gauss workflows** (50 topics × Hermes × Lean) often exceed 2 hours on free-tier APIs, or a single script runs many heavy steps in sequence.

**Fix** (any one or combine):

```bash
# Raise the limit for this shell (example: 4 hours)
export ANALYSIS_SCRIPT_TIMEOUT_SEC=14400
# Or disable per-script timeout entirely
export ANALYSIS_SCRIPT_TIMEOUT_SEC=unlimited

# Smoke: fewer topics in Gauss Sessions
export FEP_LEAN_MAX_TOPICS=5

# Skip Hermes/Lean batch: thin pipeline (catalogue + figures + vars only)
export FEP_LEAN_GAUSS_WORKFLOWS=0
```

See [configuration.md — Monorepo Stage 02](configuration.md#monorepo-stage-02-repository-root) and [pipeline.md — Timing](pipeline.md#timing).

---

## PYTHONPATH shadowing (`ModuleNotFoundError: No module named 'llm.hermes'`) {#pythonpath-shadowing}

**Symptom:** `ModuleNotFoundError: No module named 'llm.hermes'` or `ImportError: cannot import name 'HermesExplainer'` when running any `fep_lean` script.

**Root cause:** `infrastructure/llm/` exists at the monorepo root. If `infrastructure/` appears before `projects/fep_lean/src/` in `PYTHONPATH`, Python imports the infrastructure `llm` package instead of the project's `src/llm/` package, which contains `hermes.py`.

**Fix:**
```bash
# Always put projects/fep_lean/src FIRST
export PYTHONPATH="projects/fep_lean/src:.:infrastructure"

# Verify: should print the project src path, not infrastructure/llm
python -c "import llm; print(llm.__file__)"
```

When running from the monorepo root with `uv run`, prefix the command:
```bash
PYTHONPATH=projects/fep_lean/src:.:infrastructure uv run python projects/fep_lean/scripts/01_fep_catalogue_and_figures.py
```

---

## Mathlib cache timing

`lake env lean` compilation time depends heavily on whether the `.olean` cache is warm:

| Cache state | Time per topic | Notes |
| ----------- | -------------- | ----- |
| Cold (first build after clone) | 45+ minutes total | `lake build` rebuilds all `.olean` files from scratch |
| Warm (`.olean` present, Lake up-to-date) | 3–7 min total across 50 topics | Lake rechecks stamps but uses cached blobs |
| Cached (Lean compiler cache hot) | 1–2 s per topic | Steady-state in a long dev session |

**Fix cold cache:**
```bash
cd projects/fep_lean/lean
lake exe cache get    # Download prebuilt .olean from Mathlib CDN
lake build            # Only rebuilds fep_lean's own files (~30 s)
```

After `lake exe cache get` succeeds, per-topic verification drops to 1–2 s each.

---

## Diagnostic cheat sheet

| Question | Command |
| -------- | ------- |
| Which Python interpreter? | `uv run python -c "import sys; print(sys.executable)"` |
| Which packages installed? | `uv run python -m pip list` |
| Which lake binary? | `which lake; ls -la $(which lake)` |
| Mathlib cache size? | `du -sh lean/.lake/build/lib/Mathlib` (from project root) |
| Config on disk? | `cat config/settings.yaml` (from project root) |
| Are topics loading? | `uv run python -c "from catalogue.topics import FEPTopicCatalogue; print(len(FEPTopicCatalogue.from_yaml().topics))"` |
| Which env vars set? | `env \| grep -E "GAUSS\|FEP_LEAN\|HERMES\|OPENROUTER\|ANTHROPIC"` |
| What ran last? | `cat output/reports/latest/summary.json \| jq` (from project root) |

---

## Navigation

- [← Getting Started](getting-started.md)
- [Configuration →](configuration.md)
- [CLI Reference →](cli-reference.md)
- [← docs/README.md](README.md)
