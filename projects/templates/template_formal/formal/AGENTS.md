# `formal/` — Agent Guide

Repository-wide layer contract: [`../AGENTS.md`](../AGENTS.md) (`formal/` row:
"Optional Lean 4 + TLA+ side-specs, wired to `scripts/check_formal_specs.sh`
only — never decorative").

## The one invariant this directory exists to protect

**Every file under `formal/` must be reachable from
`scripts/check_formal_specs.sh`.** That wrapper and its source-owned runner are the canonical route for
these specs. Tests exercise the same runner against disposable actual copies. If you add a `.lean` or `.tla` file that
isn't exercised by that script (directly, or via a `lakefile.lean`
dependency/`.cfg` the script already runs), it is exactly the
vestigial-decoration failure mode `ISC-35`/`ISC-36` were written to catch
(`ISA.md` `## Decisions`, 2026-07-08: "RedTeam flagged vestigial-decoration
risk... ISC-35/36 force an explicit ship-or-cut decision with evidence either
way"). Wire it in or delete it — there is no third state.

**`src/template_formal/` must never grow a `formal/` subpackage again.** A
dead, never-imported `src/template_formal/formal/` stub existed at one point
and was deleted this session — confirm with `find src/template_formal
-mindepth 1 -type d -iname 'formal'` (should return nothing; note that
`find src -type d -iname '*formal*'` is the wrong check, since it also
matches `src/template_formal` itself) before touching either directory. The
project-root `formal/` documented here is the only legitimate home for this
material; a formal-spec file inside the typed `src/` surface is a regression,
not a stylistic choice, because `src/` is asserted elsewhere
(`../AGENTS.md`'s layer table) to contain only pure typed domain code with no
side-spec content.

## `scripts/check_formal_specs.sh` execution contract

The shell wrapper starts the optional platform-backed `_tool_launcher.py`
filesystem main. Its controller uses a private fresh cache; its supervised
worker additionally receives the platform pre-import executed-code audit before
calling `template_formal.tool_acceptance`. The domain package stays standalone;
the direct tool command requires the `formal-tools` platform4.0.1 extra and
blocks75 if it is unavailable. It uses the
exact source-owned Lean4.28.0 and dependency-free Lake manifest, then freshly
elaborates `AntProtocol.lean` and checks all seven printed axiom audits. TLC
checks the ideal model, fault-injected model, and deliberately broken negative
control independently. The negative control requires both exit12 and the exact
`NoFalseEstablishment` violation; an unrelated Java error cannot pass it.

Every child shares one finite total deadline (default300 seconds, maximum600),
with process-group and detached-descendant cleanup on timeout or interruption.
TLC state is disposable and trace-spec generation is disabled, so actual source
and pin identities must remain unchanged. Missing tools return75 (blocked),
invalid declarations2, failed checks1, and deadline exhaustion124. No missing
tool or formal source can become a successful skip.

Acquisition is explicit through `--acquire`; ordinary checks never implicitly
install a Lean toolchain. The same `v1.8.0` TLC release asset is bound to exact
SHA256 `7beec0f04818732a62fa193731711a99aa4f11279499b2360a7d156c519ea78d`.
The previous asset601828751 is unavailable. These replacement bytes match the
official release API's asset614143604 and an independent download on2026-10-08.
The v1.8.0 tag is a locator; the jar identifies itself as TLC2.0 (2026-10-06).
A release-page label or stale SHA1 is insufficient to admit the current asset. Cached bytes are
verified on every run; mismatches fail without executing them. Public receipts
contain actual commands, outcomes, source hashes and model output.

The formal-tool regression suite runs the same public runner against disposable
copies of these actual specs. The Python network tests exercise real seeded
in-process drop, corruption and duplication. These evidence lanes remain
independent of the kernel-checked model.

## If you add a new theorem or a new TLA+ action

- **Lean**: re-run `lake build` from `formal/lean/`, and add/update the
  trailing `#print axioms <theorem>` line for the new theorem — this is how
  the "zero sorry, zero extra axioms" claim in `lean/README.md` stays
  verified rather than asserted. See `lean/AGENTS.md` for the vacuity trap
  this file has already hit twice (`no_direct_idle_to_established`,
  `closed_only_via_known_paths`) — a new theorem's *conclusion* must be
  false for some hypothetical additional constructor, not satisfiable by a
  fixed proof term regardless of the hypothesis.
- **TLA+**: add the new invariant/property to the relevant `.cfg`'s
  `INVARIANTS`/`PROPERTIES` block (never leave it declared in the `.tla`
  module but unchecked by the `.cfg` — that is the TLA+ analogue of an
  unwired Lean theorem) and re-run `scripts/check_formal_specs.sh`. See
  `tla/AGENTS.md` for the deadlock-disabling convention (`CHECK_DEADLOCK
  FALSE`) both `.cfg` files rely on, and why it's correct here rather than a
  cover-up.

## See also

- [`README.md`](README.md) — why two formalisms, toolchain install notes
- [`lean/AGENTS.md`](lean/AGENTS.md) — Lean-specific editing rules, the vacuity trap
- [`tla/AGENTS.md`](tla/AGENTS.md) — TLA+-specific editing rules, fairness/deadlock conventions
- [`../AGENTS.md`](../AGENTS.md) — project layer contract
- [`../scripts/check_formal_specs.sh`](../scripts/check_formal_specs.sh) — the script itself
