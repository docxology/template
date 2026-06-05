# Steganography — Threat Model

> Created 2026-05-20 as part of the multi-decade-viability hardening recommended by the World Threat Model run. Until this file existed, the steganographic PDF watermarking feature was deployed without a stated threat model — that is an optics risk for a cognitive-security-adjacent operator and a real misuse-perception risk.
>
> **This file is the authoritative answer to "what does the watermarking actually do, what does it not do, and when should I use it."**

## TL;DR

- **Off by default for the public canonical exemplars.** No steganographic watermarking in the public exemplars listed in [`docs/_generated/active_projects.md`](../../docs/_generated/active_projects.md) unless explicitly enabled per-project.
- **On by default only when an operator opts in** for a specific project (e.g., pre-publication leak attribution of a confidential client deliverable).
- **The threat model below is the only thing this feature does.** Anything else (DRM, reader tracking, surveillance) is **explicitly out of scope** and not supported.

## What this watermarking IS

Cryptographic provenance metadata embedded in a PDF such that, given the processed PDF and the originating repository state, an authorized party can:

1. **Compare** the PDF against the rendered source-PDF hashes recorded in the sidecar manifest
2. **Detect** unauthorized re-distribution of a pre-publication / draft / client deliverable that was distributed via a specific channel (per-recipient watermark variant — opt-in only)
3. **Attribute** a leaked draft back to the deterministic build metadata that produced it when project/operator workflow keeps those manifests

The feature operates on the assumption that:

- The operator chose to watermark a specific document
- The operator has a legitimate reason to want post-hoc verification of provenance
- The recipients of the watermarked document have been informed (when per-recipient watermarking is used) — see "Disclosure" below

## What this watermarking IS NOT

- **Not DRM.** No attempt to prevent copying, printing, screenshotting, or quoting.
- **Not reader tracking.** No phone-home, no network call, no identifier transmitted when the PDF is opened.
- **Not surveillance of public-facing scientific work.** Public exemplars and published-via-Zenodo PDFs do not carry watermarks by default; the feature is for unpublished / pre-publication / client deliverables only.
- **Not robust against deliberate adversarial laundering.** A determined adversary can print the PDF to paper, OCR it back, re-typeset it, or pass it through a re-renderer (Ghostscript, print-to-PDF, etc.). The watermarking survives **casual redistribution** of the original PDF, not motivated re-creation. This is by design; stronger guarantees would require shifting to claim-level provenance (see [`docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) for the long-term direction).
- **Not a substitute for proper access control.** If a document is sensitive enough that leakage is unacceptable, the document should not be distributed in PDF form at all.

## Threat scenarios in scope

1. **Pre-publication draft sent to N collaborators**, one of whom leaks it to a competing group. Per-recipient watermarking lets the operator identify the leak source after the fact. Useful primarily as a deterrent, not a forensic certainty.
2. **Confidential client deliverable distributed for review.** Same shape as 1 — leak attribution via deterministic per-distribution watermark.
3. **Reproducibility provenance** — the watermark embeds deterministic build metadata and the Git commit when available, so a downstream reader (or future archivist) can identify the repository state recorded during post-processing. This is the most defensible use case and is **independent of any per-recipient identifier**.

## Threat scenarios explicitly out of scope

1. Anything involving readers of **publicly published** scientific work. Public-facing publication = no watermark.
2. Identification of readers who have not been informed they are receiving a per-recipient watermarked document.
3. Any use case where the watermarking is **not disclosed to recipients in advance**. See "Disclosure" below.
4. Use against journalists, whistleblowers, or anyone in a relationship of power asymmetry where covert watermarking would be coercive.

## Disclosure requirement

If you use per-recipient watermarking on a document, **you must disclose this to the recipients in advance**. A recommended boilerplate sentence is included in the per-project `pyproject.toml` configuration when watermarking is enabled:

> "This document is distributed with cryptographic provenance metadata that allows the originator to verify the rendered PDF and, in the case of per-recipient distribution, identify the distribution channel. No tracking or transmission occurs when the document is opened."

Failure to disclose makes this feature a surveillance tool. **Don't do that.** The cognitive-security framing this project lives inside is specifically a critique of covert manipulation; using a tool from this repo in that mode would be self-defeating and is treated as misuse.

## Robustness expectations

- **Survives:** opening in standard PDF readers, attachment to email, upload to file shares, archival to Zenodo, copying as a file
- **Probably survives:** PDF/A conversion, font subsetting, simple metadata-strip tools that target obvious metadata fields (provenance is also embedded in less-obvious places)
- **Does not reliably survive:** print-to-PDF, Ghostscript re-rendering, OCR + retypesetting, screenshot-based copying, deliberate metadata sanitization with a tool designed for that purpose, conversion to a different format (HTML, EPUB, etc.) and back

If you need robustness against the second list, you have a different problem and this is not the right tool. Consider claim-level cryptographic provenance instead (the long-term direction this repo is moving in — see Stage 10 design at [`docs/maintenance/stage-10-executable-bundle.md`](../../docs/maintenance/stage-10-executable-bundle.md)).

## Cryptographic primitives

See [`encryption.py`](encryption.py) and [`hashing.py`](hashing.py). The embedding uses standard primitives (no novel cryptography). Notes:

- Hash functions: SHA-256 and SHA-512 by default for source-PDF integrity manifests
- PDF password protection: AES-256 via `pypdf` when `encryption_enabled` and `pdf_password` are configured
- Payload encryption helpers: AES-GCM from `cryptography` for encrypted metadata payloads
- Optional fingerprinting: HMAC-SHA256 when an operator supplies a per-project secret
- The "secret" component (used for per-recipient watermarking) is a per-project key configured outside the repo — **do not commit recipient keys**

## Default configuration

Normal project rendering does **not** enable watermarking. The explicit secure-run path merges dataclass defaults, repository defaults from `infrastructure/config/secure_config.yaml`, and per-project overrides from `projects/<name>/manuscript/config.yaml` under `steganography:`.

```yaml
steganography:
  enabled: false  # set true only for confidential / pre-publication projects or secure-run defaults
  disclosure_required: true  # required when per-recipient watermarking is used
```

The public canonical exemplars do not apply steganography during normal `./run.sh` renders. Forks intending to use watermarking must opt in deliberately and must include the disclosure boilerplate.

## Why this file exists

A multi-decade-viability World Threat Model run on 2026-05-20 surfaced this feature's threat model as **underspecified** — adversaries could legitimately frame the feature as covert tracking, and the lack of a stated scope made that framing harder to refute. This file fixes that by stating the threat model explicitly, defaulting to off for public exemplars, and requiring disclosure when on.

## Related

- [`infrastructure/steganography/README.md`](README.md) — feature overview
- [`docs/security/steganography.md`](../../docs/security/steganography.md) — security context
- [`STATUS.md`](../../STATUS.md) — verification cadence for this subsystem
- [`docs/maintenance/regression-testing.md`](../../docs/maintenance/regression-testing.md) — the long-term direction for claim-level provenance
