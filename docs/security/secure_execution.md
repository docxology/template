# Secure Execution

The Secure Execution orchestrator (`secure_run.sh`) is an alternative launch point to the standard pipeline. It is a superset orchestrator: it executes the standard pipeline seamlessly, but then appends critical steganographic and cryptographic payloading post-processes.

## Verified Multi-Project Results

All three active projects have been verified to render and secure successfully:

| Project | Pages | Overlays | Barcodes | Metadata | XMP | Manifest |
|---------|-------|----------|----------|----------|-----|----------|
| `code_project` | 20 | ✅ | ✅ | ✅ (12 keys) | ✅ | ✅ |
| `cognitive_case_diagrams` | 77 | ✅ | ✅ | ✅ (12 keys) | ✅ | ✅ |
| `template` | 5 | ✅ | ✅ | ✅ (12 keys) | ✅ | ✅ |

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
# Don't run the pipeline at all, just search for existing PDF files and apply Steganography to them for the specific code_project
./secure_run.sh --project code_project --steganography-only
```

### Full Flag List

| Flag | Effect |
|------|--------|
| `--project <name>` | Select a specific project, or omit to run a multi-project sweep. |
| `--pipeline` | Bypasses the UI completely and automatically commences running. |
| `--skip-infra` | Skips running the `infra_tests/` suite (Stage 3 bottleneck). |
| `--core-only` | Skips running the `requires_ollama` LLM processing loop (Stage 7/8 bottleneck). |
| `--steganography-only` | Skips pipeline execution completely and only performs the Steganography loops. |
