# Quickstart — Active Inference

## First local checks

Prepare the declared environment through the [README quickstart](../README.md#quick-start).
For a canonical checkout, follow the
[shared preparation boundary](https://github.com/docxology/template/blob/main/projects/README.md#run-surface)
and enter `projects/templates/template_active_inference/`. For an independent
project, retain its [standalone prerequisites](../STANDALONE.md).
All commands below run from the prepared project root; initial dependencies
may need package access.

```bash
.venv/bin/python scripts/compose_manuscript.py --list-tracks
.venv/bin/python scripts/compose_manuscript.py --validate-only --strict
```

Expect track IDs/order/renderers from the first command and manifest/registry
diagnostics from the second. Validation errors return nonzero; validation-only
does not write composed Markdown or regenerate scientific producers.
Neither command supplies scientific, Lean, rendering or publication acceptance.

## Separate track refresh and complete own suite

For the full scientific/native producer sequence and existing release-profile
verification, use [Full regeneration and release verification](../README.md#full-regeneration-and-release-verification).
The narrower track refresh already documented here remains:

```bash
# Existing track-refresh order, not the first local check
.venv/bin/python scripts/generate_toy_sweep_tracks.py
.venv/bin/python scripts/generate_formal_interop_tracks.py
.venv/bin/python scripts/generate_integration_audit.py
.venv/bin/python scripts/generate_sheaf_tracks.py
.venv/bin/python scripts/z_generate_manuscript_variables.py

# Run tests
.venv/bin/python -I -m pytest tests/ --cov=src --cov-fail-under=90
```

Prepare genuine native capabilities for the selected suite and retain its
coverage/evidence obligations. These documented commands are not an observed
passing run; preserve retained public outputs and immutable receipts.
