# Secure Execution

The Secure Execution orchestrator (`secure_run.sh`) is an alternative launch point to the standard pipeline. It is a superset orchestrator: it executes the standard pipeline seamlessly, but then appends critical steganographic and cryptographic payloading post-processes.

## Verified Multi-Project Results

Post-processing is the same for every workspace returned by `discover_projects()`. **Representative row** (control-positive exemplar):

| Project | Pages | Overlays | Barcodes | Metadata | XMP | Manifest |
|---------|-------|----------|----------|----------|-----|----------|
| `template_code_project` | varies by manuscript build | ✅ | ✅ | ✅ | ✅ | ✅ |

**All other active `projects/` names:** [_generated/active_projects.md](../_generated/active_projects.md). Anything under `projects_archive/` or `projects_in_progress/` is not processed until moved into `projects/`.

The `secure_run.sh` script discovers all active projects and processes each one in sequence. Steganographic outputs include:

- `*_steganography.pdf` — augmented PDF with overlays, barcodes, and metadata
- `*.hashes.json` — SHA-256/512 hash manifest sidecar

## Interactive Mode

If you run `./secure_run.sh` with no arguments, you enter an interactive UI (similar to `./run.sh`).

The UI immediately details your active `infrastructure/config/secure_config.yaml` parameters and allows you to select which permutation to run (Fast, Core, Full, etc) with Steganography automatically affixed at the end.

### Project Selection

By default, `secure_run.sh` will target `all` discovered projects.

If you wish to only run the pipeline on one project, press `p` in the interactive menu, type the index number of the project you wish to target, and hit Enter. The subsequent run will only generate and secure PDFs for that singular project.

## Non-Interactive (CLI) Mode

For automated deployments or rapid iteration, `secure_run.sh` supports standard pipeline bypass flags:

```bash
# Run the pipeline across all projects, but skip the LLM queries and infrastructure test bottlenecks
./secure_run.sh --project all --skip-infra --core-only --pipeline
```

```bash
# Don't run the pipeline at all, just search for existing PDF files and apply Steganography to them for the specific template_code_project
./secure_run.sh --project template_code_project --steganography-only
```

### Full Flag List

| Flag | Effect |
|------|--------|
| `--project <name>` | Select a specific project, or omit to run a multi-project sweep. |
| `--pipeline` | Bypasses the UI completely and automatically commences running. |
| `--skip-infra` | Skips running the `infra_tests/` suite (Stage 3 bottleneck). |
| `--core-only` | Skips running the `requires_ollama` LLM processing loop (Stage 7/8 bottleneck). |
| `--steganography-only` | Skips pipeline execution completely and only performs the Steganography loops. |
| `--deterministic` | Pin every embedded timestamp to `git log -1 --format=%cI` so two consecutive runs produce byte-identical PDFs. Equivalent to `STEGANOGRAPHY_DETERMINISTIC=1`. |

### Deterministic / reproducible mode

For provenance audits and content-hash pinning, run with
`--deterministic`:

```bash
# Reproducible build — byte-identical *_steganography.pdf across runs
./secure_run.sh --deterministic --pipeline --project template_code_project

# Equivalent via env var
STEGANOGRAPHY_DETERMINISTIC=1 ./secure_run.sh --pipeline --project template_code_project
```

The flag pins every timestamp inside the steganography overlay (footer,
barcode payload, metadata, XMP packet, hash manifest) and the document
ID to a function of the latest commit's `%cI`. See
[`steganography.md` § Deterministic mode](steganography.md#deterministic-mode)
for trade-offs.


## See Also

- **[Security Index](../security/README.md)** — Security policies and procedures
