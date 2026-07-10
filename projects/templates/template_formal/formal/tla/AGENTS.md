# `formal/tla/` — Agent Guide

Parent layer contract: [`../AGENTS.md`](../AGENTS.md).

## The jar is never trusted on the basis of "it's already there"

`scripts/check_formal_specs.sh` fetches `tla2tools.jar` **only if it's
missing**, but it verifies the SHA-256 checksum **every single run**,
fetched-this-time or already-cached — on mismatch it deletes the file and
fails loudly rather than running an unverified jar. This closed a real
HIGH-severity finding from a round-2 adversarial pass (`ISA.md` decision log,
2026-07-09): the jar was originally fetched from a `latest`-style moving
target with zero integrity verification. If you ever change the fetch URL
(e.g. to bump the pinned TLA+ release), you **must** also update the
hardcoded `TLA_JAR_SHA256` in `../scripts/check_formal_specs.sh` to the real
checksum of that exact new release asset (`shasum -a 256` against a fresh
download) — never leave the old checksum in place "temporarily," since that
turns the check into a permanent, silent no-op that always fails (or, if you
also skip re-verifying, could accept a same-name-different-bytes asset later).
Pin to a specific dated release tag, never `latest` — a moving download
target is the whole class of supply-chain risk this discipline exists to
close.

## Deadlock disabling is a documented decision, not a workaround

Both `.cfg` files set `CHECK_DEADLOCK FALSE`. This is correct here because
both models have a genuinely terminal state (`closed` in the ideal model;
both peers' `closed` in the faulty model) with no outgoing `Next` disjunct —
TLC's deadlock detector treats "no enabled action" as a bug to report unless
told otherwise, and here it is the intended end of the protocol, not a stuck
spec. **Do not copy `CHECK_DEADLOCK FALSE` into a new `.cfg` reflexively** —
only set it when you can point to the specific state(s) that are
legitimately terminal by design; otherwise it silently hides a genuine
missing-transition bug (a state you forgot to give an exit action from).

## Fairness is deliberately asymmetric between the two specs

`AntProtocol.tla`'s `Spec` conjoins `WF_vars(Ack) /\ WF_vars(AbortHs)` because
it checks a liveness property (`HandshakeEventuallyResolves`) that promises
resolution specifically out of the `handshaking` phase — only the two actions
that *leave* that phase need to be assumed non-starved; `Open`/`AbortIdle`/
`CloseEst` get no fairness conjunct because the liveness property makes no
promise about them. `AntProtocolFaulty.tla`'s `Spec` has **no** fairness
conjuncts at all, because it only checks safety (`NoFalseEstablishment`,
`TypeOK`) — safety properties hold over every reachable state regardless of
fairness, so adding fairness there would be unnecessary complexity with no
corresponding property to justify it. If you add a liveness property to the
faulty model, you will need to work out which actions need `WF_vars`/`SF_vars`
the same way `AntProtocol.tla`'s own comment block reasons through it — don't
copy `AntProtocol.tla`'s exact fairness conjuncts without re-deriving which
actions the *new* property actually depends on resolving.

## Editing checklist

1. A new action needs: a disjunct added to `Next`, `UNCHANGED` listed for
   every variable it doesn't touch (TLC will not infer this), and — if it's
   safety-relevant — consideration of whether it needs to appear in an
   existing invariant's cases.
2. A new invariant/property needs a corresponding entry in the `.cfg`'s
   `INVARIANTS` (safety) or `PROPERTIES` (liveness — different TLA+ .cfg
   block, checked against fair behaviors of `Spec`, not just next-state
   reachability) — a property declared in the `.tla` module but absent from
   the `.cfg` is never actually checked; this is the TLA+ analogue of an
   unwired Lean theorem (see `../lean/AGENTS.md`'s vacuity discussion for why
   "declared but not exercised" is a real defect class here too).
3. Ghost/history variables (`sawHandshaking`, `iSentHello`, `rSentAck`) must
   never influence which actions are *enabled* — only real observable state
   may gate an action's guard. If a ghost variable starts appearing in a
   guard rather than only in a postcondition/invariant, it has stopped being
   a pure history flag and the model no longer matches what it claims to
   model.
4. Re-run both specs after any change and quote the real `states
   generated`/`distinct states found` numbers if you update
   `../../manuscript/05_results_discussion.md` — don't estimate or reuse a
   stale number from a previous run.
5. If you add a third `.tla` spec, add a corresponding section to
   [`README.md`](README.md) and wire it into
   `../../scripts/check_formal_specs.sh`'s `status` accumulator (see
   `../AGENTS.md`'s note on extending that script).

## Run

```bash
cd projects/templates/template_formal/formal/tla
java -jar tla2tools.jar -config AntProtocol.cfg AntProtocol.tla
java -jar tla2tools.jar -config AntProtocolFaulty.cfg AntProtocolFaulty.tla
```

Or via the combined, checksum-verified wrapper:
`scripts/check_formal_specs.sh` (runs both as the second and third of three checks).

## See also

- [`README.md`](README.md) — what each spec's variables/actions/properties mean
- [`../AGENTS.md`](../AGENTS.md) — the `formal/` directory's wiring requirement
- [`../lean/AGENTS.md`](../lean/AGENTS.md) — the sibling Lean spec's own editing rules (a useful contrast: kernel-checked proof vs. exhaustive state enumeration)
- [`../../scripts/check_formal_specs.sh`](../../scripts/check_formal_specs.sh)
