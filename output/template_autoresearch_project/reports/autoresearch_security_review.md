# AutoResearch Security Review

## Scope

- Mode: `local_deterministic`
- Network policy: `default_offline`
- Integrity algorithm: `sha256`
- External signing: `false`
- Claim scope: Local research-artifact integrity evidence for this deterministic public exemplar

## Threat Model Summary

- Assets: `7`
- Threats: `7`
- Controls: `7`

## Integrity Attestation

- Status: `passed`
- Checked files: `77`
- Missing files: `0`
- Checksum mismatches: `0`
- External signature: `false`

## Inventory Summary

- Input records: `14`
- Generated artifact records: `66`

## Non-Claims

- No external signing or Sigstore verification is performed by the default run.
- No formal SBOM standard is emitted; the inventory is SBOM-style local metadata.
- No production-grade SLSA compliance, SOC monitoring, or deployment hardening is claimed.
- No live network, LLM, or generated-code execution is part of the default path.

## Review Prompt

A human reviewer should confirm that the local checksum, inventory, and threat-model evidence is sufficient for the manuscript's limited security claims before publication.
