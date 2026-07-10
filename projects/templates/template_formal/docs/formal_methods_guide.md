# Formal Methods Guide

This template ships two optional, independent formal side-specs of the
handshake protocol — a Lean 4 model and a TLA+ specification — per
ISC-35/36's ship-or-cut decision (`## Decisions` in
[`ISA.md`](../ISA.md): "ship BOTH Lean 4 and TLA+, each wired to a real
runnable check"). Neither is decorative: both are wired into one script,
[`scripts/check_formal_specs.sh`](../scripts/check_formal_specs.sh), which
runs four checks in sequence — the Lean build, the ideal-protocol TLA+
model, the fault-injected two-peer TLA+ model, and a TLA+ negative control
(below) — and fails non-zero if any of the four fails. Both specs model the
**protocol design** independent of whether this template's Python actually
conforms to it — no claim in the manuscript conflates a passing Lean/TLA+
check with a proof about `src/template_formal/`.

## What each spec actually proves

### Lean 4 — [`formal/lean/AntProtocol.lean`](../formal/lean/AntProtocol.lean)

Seven theorems, zero `sorry`, zero axioms beyond Lean's own kernel (each
theorem's own `#print axioms` line, re-confirmed by `lake build`):

| Theorem | Claim |
| --- | --- |
| `phase_exhaustive` | The four `Phase` constructors are the only inhabitants of the type. |
| `established_requires_handshaking` | Every well-formed run reaching `established` passes through `handshaking` first — no direct `idle -> established` edge in any run. |
| `no_direct_idle_to_established` | There is no *single-step* `Step idle established` edge at all. |
| `closed_is_terminal` | No `Step` relation has `closed` as its source — the direct counterpart of "no outgoing edges from `ClosedSession`" in `protocol/session.py`. |
| `step_to_closed_cases` | Every transition *into* `closed` comes from `idle`, `established`, or `handshaking` — never anything else (a universally-quantified, falsifiable claim: a hypothetical sixth constructor targeting `closed` from elsewhere would make it false). |
| `session_token_use_succeeds` | Non-vacuity witness: a fresh `SessionToken` can be constructed and used once. |
| `cannot_reuse_consumed_token` | The affine-discipline counterpart to `SessionConsumedError`: no well-typed proof term can license consuming an already-`use`d token's result again. |

### TLA+ — [`formal/tla/AntProtocol.tla`](../formal/tla/AntProtocol.tla) and [`AntProtocolFaulty.tla`](../formal/tla/AntProtocolFaulty.tla)

`AntProtocol.tla` models a single connection's phase state machine (the
same five states/edges as the Lean model) and checks, via TLC:

- `SafetyInvariant` (basic well-formedness) and
  `EstablishedRequiresHandshaking` — the TLA+ counterpart of
  `established_requires_handshaking`.
- `HandshakeEventuallyResolves` — a **liveness** property
  ($\Box(\text{handshaking} \Rightarrow \Diamond(\text{established} \lor
  \text{closed}))$), which only holds relative to the weak-fairness
  conjuncts (`WF_vars(Ack)`, `WF_vars(AbortHs)`) added to `Spec` — without
  them, TLC would permit a "coward" run that stalls in `handshaking`
  forever via stuttering.

`AntProtocolFaulty.tla` is a **separate, genuinely new** model — not a copy
of `AntProtocol.tla` — with an explicit two-peer message channel as
first-class state (`msgs`, `delivered`) and
`SendHello`/`ReceiveHello`/`ReceiveAck`/`Corrupt`/`DeliverCorrupt`/`Duplicate`
actions mirroring `network/bus.py`'s real drop/corrupt/duplicate fault
modes. It checks `NoFalseEstablishment` — a peer is never `established`
without the other peer's real message having actually been sent, even
under arbitrary fault interleaving — the direct TLA+ analogue of ISC-23/24.

**What `NoFalseEstablishment` actually guards — send-provenance, not
content-integrity (ISC-105).** A RedTeam pass proved by direct mutation
test that the invariant, as originally described in the manuscript, was
overclaimed: widening `ReceiveHello`'s guard to also accept a
`"corrupt"`-tagged frame enlarges the reachable state space (92 → 136
distinct states) yet `NoFalseEstablishment` still reports zero violations.
That is because the invariant is built entirely on `iSentHello`/`rSentAck`
— pure send-side history flags, set once by a genuine send and never
reset — so it certifies **send-provenance** ("a real message was genuinely
sent by the other peer, at some point"), not **content-integrity**
("the specific delivered frame was uncorrupted"). See
[`manuscript/05_results_discussion.md`](../manuscript/05_results_discussion.md)'s
Theorem 12, clause (iii), for the corrected wording.

### TLA+ negative control — [`AntProtocolFaultyNegControl.tla`](../formal/tla/AntProtocolFaultyNegControl.tla)

A permanent, **deliberately broken** sibling of `AntProtocolFaulty.tla` —
verbatim copy plus one added action, `ForgeHello`, which injects a
`[kind |-> "hello", sender |-> "I"]` message onto the channel *without*
setting `iSentHello` (an unauthenticated/spoofed hello the initiator never
actually sent). This is the TLA+ analogue of the mypy-oracle's
`tests/mypy_fixtures/bad_*.py` fixtures: without a negative control, "TLC
checked `NoFalseEstablishment` and found no violation" says nothing about
whether the invariant *can* detect the vulnerability class it advertises.

`scripts/check_formal_specs.sh` runs TLC against it with **inverted**
pass/fail logic: a reported `Invariant NoFalseEstablishment is violated`
is `PASS` (the expected 3-state trace `Init -> ForgeHello ->
ReceiveHello` establishes `rPhase` while `iSentHello` is still `FALSE`); a
clean "no error found" is `FAIL`, because it would mean the negative
control itself is vacuous. TLC's own exit code is not used directly for
this check (a genuine violation makes it non-zero); the script captures
the output text via `|| true` and greps it for the violation string.

All three TLA+ models are re-run as part of `check_formal_specs.sh` (Lean:
`lake build`; TLA+: TLC against each `.cfg`, in order — ideal protocol,
faulty two-peer, then the negative control with inverted logic). Requires
`lake`/`elan` on `PATH` and a Java runtime for TLC (`FORMAL_JAVA_BIN`
overrides the binary).

## Running the checks

```bash
uv run bash projects/templates/template_formal/scripts/check_formal_specs.sh
```

`tla2tools.jar` is **not** committed (a multi-MB binary has no place in a
strongly-typed *source* template) — the script fetches it on first run
from a pinned, dated `tlaplus/tlaplus` release tag (never `latest`) and
verifies its SHA-256 before any `java -jar` invocation; a checksum mismatch
deletes the file and fails loudly (see the
[security guide](security_guide.md) for the full story). The jar is cached
under `formal/tla/` (gitignored) after the first successful fetch.

## Extending either spec safely: the near-vacuity lesson (read this before adding a theorem)

This template learned the same lesson **three times now** — twice in Lean,
and a third time in TLA+, on a different formalism entirely — which is
itself the point: fixing one instance does not immunize the rest of the
spec. From [`ISA.md`](../ISA.md)'s Changelog, `AntProtocol.lean`'s own
docstrings, and `AntProtocolFaultyNegControl.tla`'s header:

**First occurrence.** An earlier revision had a theorem named
`no_skip_to_established`, intended to state "there is no direct
`idle -> established` edge." As actually written, it reduced to a
restatement of `established_requires_handshaking` via a vacuously-true
`Reaches idle idle` conjunct — the theorem's *name* promised a one-step
non-existence claim, but its *content* didn't state it. It was replaced
with `no_direct_idle_to_established`, which states the one-step claim
directly (`¬ Step idle established`, discharged by `cases` finding no
matching constructor).

**Second occurrence, same class, different theorem.** A second
cross-vendor audit pass later caught `closed_only_via_known_paths`
carrying the *identical* vacuity class in a different theorem: it
concluded a three-way disjunction
`Reaches idle established ∨ Reaches idle idle ∨ Reaches idle handshaking`,
and `Reaches idle idle` is unconditionally provable via `Reaches.refl`
regardless of which run was passed in — so the whole disjunction was
satisfiable by a fixed proof term that never inspected its hypothesis.
Rewording the conclusion to reference the run's own extracted predecessor
phase did not escape the trap either, because in this small, four-phase
state machine every candidate predecessor is trivially reachable from
`idle` by *some* path independent of the specific run — the
`Reaches`-wrapped framing is inherently satisfiable regardless of
hypothesis in this model. The theorem was **removed rather than patched a
second time**; the genuinely load-bearing, falsifiable content underneath
it — a direct, universally-quantified claim about the `Step` relation
itself, with no `Reaches` wrapper — was promoted to a named,
`#print axioms`-checked theorem in its place: `step_to_closed_cases`. The
theorem count stayed at seven; the set of what is proved changed to remove
the vacuous member.

**Third occurrence, same class again, a different formalism (ISC-105).**
A RedTeam pass and a direct mutation test caught the identical shape of
defect a third time, this time in TLA+, not Lean: `AntProtocolFaulty.tla`'s
`NoFalseEstablishment` invariant was described in the manuscript as holding
"under arbitrary drop/corrupt/duplicate fault interleaving" — read as a
content-integrity guarantee. Widening `ReceiveHello`'s guard to also accept
a `"corrupt"`-tagged frame enlarged the reachable state space (92 → 136
distinct states) yet the invariant still reported zero violations, because
it is built entirely on `iSentHello`/`rSentAck` — send-side history flags
that never depend on whether the *specific delivered* frame was corrupted.
The invariant was not vacuous outright (it does detect genuine
send-provenance violations, as the new negative control below proves), but
the manuscript's *description* of what it guarded was broader than what it
actually checked — the same "name/description promises more than the
content delivers" shape as both Lean occurrences. Fixed two ways: the
manuscript's wording was corrected to "send-provenance" precisely, and
(unlike the two Lean occurrences, which were fixed by rewording or
replacing a theorem) a permanent negative control,
[`AntProtocolFaultyNegControl.tla`](../formal/tla/AntProtocolFaultyNegControl.tla),
was added so the invariant's real detection power is proven by a passing
check, not merely asserted in prose — see the section above.

**The generalizable lesson** (`ISA.md`, round-2 Decisions entry, reconfirmed
by the round-6 TLA+ occurrence): fixing one instance of a defect class does
not immunize the rest of the file — or the sibling spec in a different
formalism — against the same class. A rule-shaped defect (`# type: ignore`
audits, a mock grep) generalizes automatically once fixed once; a
*proof-shape* defect does not — it needs a fresh look at every theorem or
invariant of similar shape, not just the one already caught, and not only
within the file where it was first found.

**Practical checklist before adding a new Lean theorem here:**

1. State the claim as directly as possible — prefer a universally-quantified
   fact about the relation itself (`Step`/`Reaches`) over a disjunction
   wrapped in a reachability predicate that this small state machine can
   satisfy unconditionally.
2. Ask: is this conclusion provable by a **fixed** proof term regardless of
   the hypothesis? If yes, it's vacuous, no matter how it's named.
3. Re-run `lake build` and read every `#print axioms` line — a theorem
   compiling and printing zero extra axioms is necessary, not sufficient;
   it does not by itself prove the conclusion is non-vacuous.
4. If a hypothetical violation (a sixth `Step` constructor, an extra edge)
   would make the theorem false, it's real. If no counterexample is even
   expressible in the model, look harder before shipping it.

The same discipline applies to a new TLA+ invariant/property: before
trusting a green TLC run, check whether the property could pass on a
model where the mechanism it's supposed to guard is broken. Being checked
against a model with real fault actions is necessary but not sufficient —
`NoFalseEstablishment` is checked against exactly such a model
(`AntProtocolFaulty.tla`) and was still overclaimed until the third
occurrence above was found and a dedicated negative control was built. The
real test is the one `AntProtocolFaultyNegControl.tla` now performs
directly: construct a model where the specific guarantee you're claiming
is actually broken, and confirm TLC reports a violation. If you cannot
construct such a model, the invariant may be checking something narrower
or different than what its name/description claims.
