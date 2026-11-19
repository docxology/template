# Quickstart — template_sia

## First fixture replay: prepared project root

For an independent checkout, follow the genuine SDK-wheel recipe in
[STANDALONE.md](../STANDALONE.md#standalone-environment). For a canonical
checkout, prepare Root and this project's own environment through the
[shared run surface](https://github.com/docxology/template/blob/main/projects/README.md#run-surface),
then enter `projects/templates/template_sia/`. Initial dependency preparation
may need package access; the default replay does not require a model service.

```bash
.venv/bin/python scripts/run_sia_loop.py
.venv/bin/python scripts/z_generate_manuscript_variables.py
```

The replay prints report/summary paths and a generation count. It demonstrates
the fixture-backed loop, not model performance or complete native acceptance.

## Separate monorepo stage operations

Return to the prepared monorepo root. These repository scripts are not shipped
in an independent project; see the
[dispatch guide](https://github.com/docxology/template/blob/main/docs/RUN_GUIDE.md).

```bash
# Selected project test lane
uv run --no-sync --offline python scripts/pipeline/stage_01_test.py --project templates/template_sia --project-only

# Analysis only
uv run --no-sync --offline python scripts/pipeline/stage_02_analysis.py --project templates/template_sia

# Existing selected core pipeline, without its infrastructure-test stage
uv run --no-sync --offline python scripts/runner/execute_pipeline.py --project templates/template_sia --mode core --skip-infra
```

## Bounded live numeric proposals (optional)

Run the following command from the prepared project root, not the monorepo root.
With Docker, an immutable local Python image ID, and the selected model already
available from a loopback Ollama service:

```bash
.venv/bin/python scripts/run_sia_loop.py --live-proposals \
  --model <local-model-name> --container-image sha256:<existing-local-image-id> \
  --proposal-output-dir output/live_proposals_example
```

The CLI model overrides `project_config.sia.llm_model`; the shipped empty value
requires an explicit selection. No tool, image, or model is downloaded by the
command. Missing capabilities block with exit 75. The target runs only in the
restricted Docker container. Its numeric mutation scope, exact rollback,
held-out boundary, and receipt files are described in
[`live-numeric-proposals.md`](live-numeric-proposals.md).

`--live-sia` executes unchanged reference subprocess diagnostics. Its optional
feedback note supplies no mutation or sandbox acceptance.

Default pipeline and CI use fixture replay (`live: false` in `manuscript/config.yaml`).

## Deliverables

- First fixture report: `output/reports/sia_loop_report.md` relative to the
  project root (`projects/templates/template_sia/output/reports/sia_loop_report.md`
  relative to the monorepo root).
- Copied combined PDF, only after the selected monorepo pipeline/rendering:
  `output/templates/template_sia/pdf/template_sia_combined.pdf` relative to the
  monorepo root.

Complete selected tests still require their declared Docker/image capabilities;
actual Ollama acceptance additionally requires its prepared model service.
Missing capabilities must not be converted into complete acceptance through
skips. See [Optional hardening](../README.md#optional-hardening).
