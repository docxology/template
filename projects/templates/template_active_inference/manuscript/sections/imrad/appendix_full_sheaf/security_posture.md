The appendix includes the security posture as a release-boundary proof object.
Each row in `output/reports/security_posture_audit.json` has evidence artifacts,
validators, a scoped boundary statement, and a negative-control identifier. The
negative controls target the verifier failure modes a well-resourced adversary
would prefer: aggregate forgery, untracked credentials, network-derived evidence,
private-data leakage, unsigned production-release claims, and production
zero-trust claims without a runtime identity plane.

The posture is therefore defensive and local: it hardens this public template
against evidence laundering, artifact drift, secret exposure, and false release
claims while keeping production-only controls deferred until a real deployment
adds signed provenance, SBOMs, identity-aware access, telemetry, and incident
response evidence.
