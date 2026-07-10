# Steganography Module — Agent Documentation

## Overview

The `infrastructure/steganography` module provides optional, configurable
steganographic augmentation of PDF outputs. It post-processes existing PDFs
to produce a second `*_steganography.pdf` that embeds security overlays,
barcodes, metadata, hash values, and optional encryption.

## Key Classes

### `SteganographyConfig` (`config.py`)

Dataclass with boolean toggles for each technique. Factory methods:

- `from_dict(data)` — parse from YAML config section
- `all_enabled()` — return a config with everything on

### `resolve_build_timestamp(*, deterministic=None, repo_root=None)` (`config.py`)

Single source of truth for the build timestamp embedded in overlays,
footers, barcode payloads, XMP packets, and hash manifests.

* `deterministic=True` (or `STEGANOGRAPHY_DETERMINISTIC=1` in the
  environment with `deterministic=None`) — returns
  `git log -1 --format=%cI` from `repo_root` (defaults to `Path.cwd()`).
  Same `HEAD` ⇒ same timestamp ⇒ byte-identical
  `*_steganography.pdf` across runs.
* Otherwise — current UTC wall-clock time as `YYYY-MM-DDTHH:MM:SSZ`.
* Missing `git` or non-zero exit ⇒ logs a single warning and falls back
  to wall-clock time. **Trade-off:** deterministic mode trades a fresh
  per-run timestamp for reproducibility — combine with the
  `*.hashes.json` manifest when both are needed.

### `SteganographyProcessor` (`core.py`)

Orchestrator. Call `process(input_pdf, output_pdf, title, authors, keywords)`.
Chains: hashing → overlays → barcodes → metadata → encryption → manifest.

## File Map

| File | Responsibility |
|------|---------------|
| `config.py` | `SteganographyConfig` dataclass |
| `core.py` | `SteganographyProcessor` orchestrator |
| `overlays.py` | Watermark, footer, invisible text (reportlab) |
| `barcodes.py` | QR, Code128, barcode strips (public API) |
| `barcode_generators.py` | Low-level barcode image generators |
| `barcode_payload.py` | Barcode payload encoding and structure |
| `metadata.py` | PDF Info + XMP injection (pypdf) |
| `hashing.py` | SHA-256/512, manifest JSON |
| `encryption.py` | AES-GCM payload helpers, HMAC, AES-256 PDF password protection |
| `kmyth_adapter.py` | Optional Kmyth/TPM validation and `.ski` sidecar sealing |
| `kmyth/` | Git submodule for upstream `NationalSecurityAgency/kmyth` C sources |
| `swtpm_mssim_proxy.py` | TCP proxy bridging mssim TCTI protocol to swtpm's socket protocol (macOS) |
| `start_tpm_backend.py` | Launcher script for swtpm + proxy (init, start, stop, check) |

## Integration Points

- **`infrastructure/__init__.py`** — lazy import under try/except
- **`infrastructure/core/config/loader.py`** — `SteganographyConfigYAML` TypedDict in `ManuscriptConfig` (defined in `infrastructure/core/config/schema.py`)
- **`secure_run.sh`** — shell entry; `uv sync --group steganography`, then `python -m infrastructure.orchestration secure` ([`run_secure_pipeline`](../orchestration/secure_run.py)); pipeline DAG matches `./run.sh` via Python, not a `./run.sh` subprocess
- **`infrastructure/config/secure_config.yaml`** — repository secure-run defaults
- **`config.yaml`** — project `manuscript/config.yaml` `steganography:` section with per-technique booleans and overrides
- **Kmyth optional preflight** — `./secure_run.sh --validate-kmyth [--project <name>]` validates `kmyth-seal` / `kmyth-unseal` from `kmyth_binary_dir`, the submodule `bin/`, or `PATH` without running the pipeline

## Dependencies

All Python dependencies are lazily imported: `pypdf`, `reportlab`, `qrcode[pil]`, `python-barcode`, `cryptography`.

Kmyth is not installed by `uv sync`. It is a git submodule at
`infrastructure/steganography/kmyth`; build it with `make -C
infrastructure/steganography/kmyth` or install Kmyth separately on `PATH`
before enabling `kmyth_enabled: true`.

## TPM Backend Setup (macOS)

macOS has no hardware TPM. To use Kmyth sealing on macOS, a software TPM
emulator (swtpm) must be running and a protocol-bridging proxy must
translate between the mssim TCTI wire protocol (used by TPM2-TSS) and
swtpm's native socket protocol.

### Prerequisites

1. **swtpm**: `brew install swtpm`
2. **TPM2-TSS libraries**: Built at `~/.kmyth-prefix/lib` (headers at
   `~/.kmyth-prefix/include`)
3. **Kmyth binaries**: Built at `infrastructure/steganography/kmyth/bin/`

### Quick Start

```bash
# Start the TPM backend (swtpm + proxy)
eval "$(python3 infrastructure/steganography/start_tpm_backend.py start)"

# Run the pipeline with Kmyth sealing
uv run python projects/templates/template_redacted_report/scripts/generate_dev_variants.py \
    --kmyth-binary-dir infrastructure/steganography/kmyth/bin \
    --kmyth-timeout-seconds 15

# Stop the TPM backend when done
python3 infrastructure/steganography/start_tpm_backend.py stop
```

### How It Works

The mssim TCTI in TPM2-TSS sends TPM commands using the Microsoft
Simulator wire protocol on two TCP channels:

- **Control port** (default 2322): platform commands (POWER_ON=1,
  NV_ON=11, TPM_SESSION_END=20) as 4-byte big-endian uint32 values
- **Data port** (default 2321): TPM commands wrapped in a 9-byte header
  (4B cmd_type=MS_SIM_TPM_SEND_COMMAND + 1B locality + 4B tpm_size)

swtpm uses a different socket protocol (CMD_* enum on control channel,
raw TPM commands on data channel). The proxy (`swtpm_mssim_proxy.py`)
bridges these two protocols:

- Control: intercepts platform commands and returns success (swtpm's
  `--flags startup-clear` handles TPM initialization)
- Data: strips the 9-byte mssim header, forwards raw TPM commands to
  swtpm, and wraps responses back in mssim format

### Architecture

```
kmyth-seal → mssim TCTI → [proxy:2321/2322] → [swtpm:3321/3322]
                              ↑ protocol bridge     ↑ software TPM
```

### Kmyth Source Patch (FlushContext)

The upstream kmyth-seal does not flush transient TPM objects (storage
keys) after sealing, which exhausts swtpm's limited transient object
slots (~3) on the next invocation. The kmyth source at
`kmyth/src/tpm/kmyth_seal_unseal_impl.c` has been patched to call
`Tss2_Sys_FlushContext` for the storage key handle before
`free_tpm2_resources`.

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `TSS2_TCTI_DEFAULT` | TCTI connection string (e.g., `mssim:host=127.0.0.1,port=2321`) |
| `DYLD_LIBRARY_PATH` | Path to TPM2-TSS `.dylib` and `.so` files (`~/.kmyth-prefix/lib`) |

The `start_tpm_backend.py` script prints these for `eval`. The
`kmyth_adapter.py` also sets them automatically when
`KmythSealOptions.tcti_config` is provided.

## Testing

```bash
uv run pytest tests/infra_tests/steganography/ -v
```
