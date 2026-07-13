# data - template_redacted_report

Invented public redaction fixtures live here. Keep segments, redaction decisions, and review records synthetic or cleared; do not commit high-side source text.

`example_segments.json` is loaded by a strict typed contract. Segment IDs,
source-control labels, roles, and release authority must be public-safe
identifiers; the release policy must be `intelligence_release_review`, the
ceiling must match that policy, and public replacements must remain the literal
`[REDACTED]` token.
