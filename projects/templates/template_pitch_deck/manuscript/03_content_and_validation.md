# Content and Validation {#sec:validation}

## Methods


## The flagship pitch

The shipped content pitches [`template_template`](../../template_template/) — this
monorepo's autopoietic meta-project, which introspects the repository's own
architecture and regenerates its manuscript from live counts — to a
meta-science and science-integrity audience. Every length follows the same
arc: the problem (research communication and reproducibility are
under-tooled), the solution (a two-layer, thin-orchestrator monorepo with a
90%/60% coverage floor, no-mocks testing, and multi-platform publication),
proof (real, currently-measured facts: exemplar count, coverage floors, the
publishing surface `template_template` itself already reaches), and an ask.
Medium and long variants add landscape, architecture, and roadmap detail;
long adds a full governance/confidentiality walkthrough and an appendix.

## Token resolution

`src/token_resolution.py` implements the same `{{TOKEN}}` convention used by
`infrastructure/rendering/manuscript_injection.py`
(`\{\{[A-Z][A-Z0-9_]*\}\}`), scoped to `manuscript/deck_content_*.yaml`
instead of `manuscript/*.md`. `resolve_tokens` raises if any token in the
content has no matching key in the live token set from `src/deck_tokens.py` — mirroring
`template_madlib`'s `test_all_manuscript_tokens_are_generated` pre-substitution
coverage check, adapted to deck content. `scripts/10_audit_deck_content.py`
runs this check plus the cliché lint in one pass and exits non-zero on either
class of failure; both failure modes are proven to actually fire (a
deliberately-broken fixture triggers each) before the real content is
checked clean.

## Cliché lint

`src/cliche_lint.py` maintains a word-boundary-safe denylist of pitch-deck
stock phrases ("synergy," "disrupt," "10x," "game-changing," "rocket ship,"
"paradigm shift," and more). It is checked against every resolved slide
across all three lengths as part of the same audit script, and — like the
token check — is proven to fire on a deliberately cliché-laden sentence
before the real content's cleanliness is trusted.
