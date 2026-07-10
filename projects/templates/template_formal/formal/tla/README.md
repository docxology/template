# `formal/tla/` — TLA+ specs of the handshake protocol

Two independent TLA+ modules, checked by TLC (the TLA+ model checker), model
the same handshake protocol from two different angles:

| File | Model | Peers | What's new vs. the other model |
| --- | --- | --- | --- |
| `AntProtocol.tla` / `.cfg` | The **ideal** single-connection state machine — the direct TLA+ counterpart of `AntProtocol.lean` | 1 (a single `phase` variable) | Safety invariants plus a real **liveness** property under weak fairness |
| `AntProtocolFaulty.tla` / `.cfg` | A **two-peer** protocol with an explicit, fault-injectable message channel, mirroring `network/bus.py`'s drop/duplicate/corrupt fault modes and `protocol/session.py`'s asymmetric initiator/responder handshake | 2 (initiator `I`, responder `R`, plus channel state `msgs`/`delivered`) | Genuinely new modeling work, not a two-copy of the ideal model — there is no single `phase` variable or `sawHandshaking` ghost flag here; the safety property is about **cross-peer message provenance**, not one machine's own transition history |

Both are **state-machine-level models** (per the ISA's stated Out of Scope):
no real sockets, no real multi-process execution, no consensus protocol.
`msgs` in `AntProtocolFaulty.tla` is an in-process abstract channel — the
TLA+ analogue of the real `InProcessBus[MsgT]`, not a network simulation.

## `AntProtocol.tla` — ideal model

State: `phase \in {"idle", "handshaking", "established", "closed"}` plus a
ghost history flag `sawHandshaking` (set `TRUE` on entering `handshaking`,
never reset — pure bookkeeping, does not affect which transitions are
enabled). Five actions mirror the Lean `Step` constructors exactly: `Open`,
`Ack`, `CloseEst`, `AbortIdle`, `AbortHs`.

Checked by `AntProtocol.cfg`:

- **`SafetyInvariant`** (`TypeOK`) — basic well-formedness.
- **`EstablishedRequiresHandshaking`** — `phase = "established" => sawHandshaking`,
  the direct TLC cross-check of the Lean theorem `established_requires_handshaking`.
- **`HandshakeEventuallyResolves`** (a `PROPERTIES`, not `INVARIANTS`, entry —
  TLA+ .cfg syntax requires liveness properties to live in a separate block) —
  `[](phase = "handshaking" => <>(phase \in {"established", "closed"}))`: once
  a handshake is pending it does not stall forever. This only holds because
  `Spec` conjoins `WF_vars(Ack) /\ WF_vars(AbortHs)` — without weak fairness,
  TLC's exists-a-behavior semantics permits a "coward" run that stutters in
  `handshaking` forever, which would make this property vacuously unprovable.
- `CHECK_DEADLOCK FALSE` — `closed` is *deliberately* terminal (no outgoing
  `Next` disjunct); that is a real dead end of the protocol, not a spec bug,
  so TLC's deadlock detector is turned off rather than papering over a
  legitimate stuck state.

## `AntProtocolFaulty.tla` — fault-injected two-peer model

State: `iPhase`, `rPhase` (initiator/responder phases — deliberately
asymmetric domains, `IPhases` includes `"handshaking"` but `RPhases` does
not, mirroring the real code's asymmetric `IdleSession.open()` vs.
`IdleSession.accept_hello()`), `msgs` (in-flight message set), `delivered`
(messages that have genuinely caused a real phase transition), and two ghost
flags `iSentHello`/`rSentAck` recording whether a *real* (uncorrupted)
message was ever actually sent.

Actions: `SendHello`, `ReceiveHello`, `ReceiveAck` (each with a nondeterministic
deliver-or-drop branch modeling the "drop" fault mode), `Corrupt` (mangles an
in-flight message's `kind` tag, mirroring `FaultInjector.corrupt()`'s wire-byte
XOR), `DeliverCorrupt` (a corrupted frame is discarded with no phase
transition, mirroring `try_recv` returning `Result.Err(MalformedMessage(...))`),
`Duplicate` (replays an **already-delivered** message back onto the channel —
deliberately the harder case: it proves a genuine past message replayed later
cannot force a second illegitimate establishment, because the phase guards
`ReceiveHello`/`ReceiveAck` depend on are no longer satisfied once the real
handshake has resolved), `CloseInitiator`, `CloseResponder`.

Checked by `AntProtocolFaulty.cfg`:

- **`TypeOK`** — well-formedness across all seven state variables.
- **`NoFalseEstablishment`** — `(rPhase \in {"established","closed"}) =>
  iSentHello` and the symmetric `iPhase` clause: a peer is never established
  (or having-been-established, via `closed`) without the other side's real
  message genuinely having been sent, under *any* interleaving of
  drop/duplicate/corrupt faults. This is the direct TLA+ analogue of what
  `ISC-23`/`ISC-24` test in Python — cross-peer provenance, not merely "a
  message with the right tag currently sits in the channel" (which drop/corrupt
  alone could make trivially false without saying anything about history).
- `CHECK_DEADLOCK FALSE` — same reasoning as the ideal model: both peers'
  `closed` phases are legitimately terminal once torn down.

No `Spec` fairness conjuncts are added here (unlike `AntProtocol.tla`) — this
model checks safety only, not a liveness property, so weak fairness isn't
needed for TLC to find a meaningful counterexample if `NoFalseEstablishment`
were violated.

## Running TLC directly

`tla2tools.jar` is **not committed** — a multi-MB binary has no place in a
strongly-typed *source* template. `scripts/check_formal_specs.sh` fetches it
on first run from a pinned, dated release tag
(`tlaplus/tlaplus` `v1.8.0`, never `latest`) and verifies its SHA-256 before
ever invoking it (see [`../AGENTS.md`](../AGENTS.md)). Once
`tla2tools.jar` is present in this directory (fetched by the script, or
downloaded yourself and checksum-verified the same way), you can run either
spec directly without the wrapper:

```bash
cd projects/templates/template_formal/formal/tla

# Ideal single-peer model (safety + liveness)
java -jar tla2tools.jar -config AntProtocol.cfg AntProtocol.tla

# Fault-injected two-peer model (safety only)
java -jar tla2tools.jar -config AntProtocolFaulty.cfg AntProtocolFaulty.tla
```

A successful run ends with `Model checking completed. No error has been
found.` and reports the number of states generated/distinct states found —
quote these numbers, don't estimate them, if you cite a run in the
manuscript (`../../manuscript/05_results_discussion.md`). TLC's scratch
output directory (`states/`) is gitignored.

## See also

- [`AGENTS.md`](AGENTS.md) — editing rules, fairness/deadlock conventions
- [`../README.md`](../README.md) — why this sits beside a separate Lean spec
- [`../../scripts/check_formal_specs.sh`](../../scripts/check_formal_specs.sh) — the checksum-pinned jar fetch + both TLC invocations
- [`../../src/template_formal/network/bus.py`](../../src/template_formal/network/bus.py) — the real fault-injecting bus `AntProtocolFaulty.tla` mirrors
- [`../../src/template_formal/protocol/session.py`](../../src/template_formal/protocol/session.py) — the real session state machine both specs mirror
