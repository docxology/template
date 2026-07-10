# `formal/` — Agent Guide

Repository-wide layer contract: [`../AGENTS.md`](../AGENTS.md) (`formal/` row:
"Optional Lean 4 + TLA+ side-specs, wired to `scripts/check_formal_specs.sh`
only — never decorative").

## The one invariant this directory exists to protect

**Every file under `formal/` must be reachable from
`scripts/check_formal_specs.sh`.** That script is the *only* thing that runs
these specs — no pipeline stage, pytest fixture, or CI job invokes `lake` or
`java -jar tla2tools.jar` on its own. If you add a `.lean` or `.tla` file that
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

## `scripts/check_formal_specs.sh` — what it actually does, in order

1. `cd formal/lean && lake build` — Lean 4 kernel-checks
   `AntProtocol.lean`. Exit non-zero fails the whole script (`status=1`, but
   the script keeps going to report the TLA+ side too before its final exit).
2. Checks `java` is on `PATH` (or `$FORMAL_JAVA_BIN`) — fails loudly rather
   than silently skipping if the binary is missing.
3. Fetches `formal/tla/tla2tools.jar` **only if it isn't already present** —
   from a specific dated GitHub release tag (`v1.8.0`), never `latest`.
4. **Always** verifies the fetched-or-cached jar's SHA-256 against a
   hardcoded checksum before ever invoking `java -jar` against it — on
   mismatch it deletes the file and fails; a stale, corrupted, or tampered
   cached jar is never silently trusted just because it already existed on
   disk from a prior run.
5. Runs TLC against `AntProtocol.tla` (`AntProtocol.cfg`) — the ideal
   single-peer model.
6. Runs TLC against `AntProtocolFaulty.tla` (`AntProtocolFaulty.cfg`) — the
   fault-injected two-peer model.
7. Exits non-zero if **any** of the three checks failed; each PASS/FAIL is
   echoed individually so a partial failure is diagnosable without re-running
   the whole script.

Do not add a fourth sub-check to this script without also adding its own
independent PASS/FAIL echo and letting it participate in the shared
`status` accumulator — the script's whole value is that one exit code
covers every spec in this directory, and that only holds if every new spec
is actually wired into it the same way.

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
