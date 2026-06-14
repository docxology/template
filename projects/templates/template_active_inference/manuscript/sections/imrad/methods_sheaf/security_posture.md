The security-posture track treats the public exemplar itself as the defended asset.
`output/reports/security_posture_audit.json` records {{security_posture_control_count}}
controls: {{security_posture_enforced_count}} enforced local controls and
{{security_posture_deferred_count}} production-security obligations that are explicitly
deferred rather than claimed. The enforced rows cover public-data boundaries,
offline reproducibility, artifact hashes, copied-output parity, claim/scope
traceability, the Lean boundary, and a source/config secret-pattern scan.

The audit is intentionally not a production certification. It records
{{security_posture_high_risk_gap_count}} high-risk local gaps and
{{security_posture_secret_finding_count}} high-risk secret-pattern findings; the
all-controls flag is `{{security_posture_all_controls_ok}}`, and all listed
evidence is present: `{{security_posture_all_evidence_present}}`. Deferred rows
cover signed provenance/SBOM release attestation and zero-trust runtime controls,
which require deployment-specific identity, device posture, logging, and signing
infrastructure outside this toy-only manuscript.
