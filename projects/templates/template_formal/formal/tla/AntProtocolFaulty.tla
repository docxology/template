------------------------ MODULE AntProtocolFaulty ------------------------
(* Two-peer TLA+ model of the same handshake protocol modeled in
   AntProtocol.tla/AntProtocol.lean, but this time with an explicit,
   fault-injectable message channel between an initiator ("I") and a
   responder ("R") -- the direct TLA+ analogue of the real
   `network/bus.py` fault-injecting bus and its four independently
   toggleable fault modes (drop, reorder/duplicate, corrupt), and of the
   real handshake in `protocol/session.py`:

     I: Idle --SendHello--> Handshaking --ReceiveAck--> Established
     R: Idle --ReceiveHello (also sends the ack)--> Established

   mirroring the real (deliberately asymmetric) code: `IdleSession.open()`
   moves the initiator only as far as `HandshakingSession`, while
   `IdleSession.accept_hello()` moves the responder straight to
   `EstablishedSession` in the same call that produces the `hello_ack` to
   send back (see `protocol/session.py`). Both peers can independently
   close from "established".

   This module models the actual message *channel* as first-class state
   (`msgs`), not just the two peers' local phases, which is what makes
   Send/Deliver/Duplicate/Corrupt meaningful actions rather than a single
   atomic step per phase transition, as in the simpler single-peer
   AntProtocol.tla. This is genuinely new modeling work, not a two-copy of
   AntProtocol.tla: there is no single "phase" variable here, no
   `sawHandshaking` ghost flag, and the safety property below is about
   cross-peer message provenance, not about one machine's own transition
   history.

   Out of scope, per the ISA: no real sockets, no real multi-process
   execution -- `msgs` is an in-process, abstract channel exactly like the
   real `InProcessBus[MsgT]`. *)

EXTENDS Naturals, FiniteSets

Senders == {"I", "R"}
Kinds == {"hello", "hello_ack", "corrupt"}

(* A message record is fully identified by (kind, sender) in this
   single-shot (no retry-with-fresh-content, no session reopening) model,
   so no unique message-id field is needed: the two genuine messages that
   can ever exist are exactly [kind |-> "hello", sender |-> "I"] and
   [kind |-> "hello_ack", sender |-> "R"]. Representing messages as
   structural records in a *set* (rather than a sequence/bag with unique
   ids) keeps the state space finite by construction -- Duplicate re-adds
   a record already present in `delivered`, which a set absorbs without
   needing an unbounded counter, while still making duplication an
   observable, non-vacuous action (see Duplicate below). *)
Message == [kind: Kinds, sender: Senders]

VARIABLES iPhase, rPhase, msgs, delivered, iSentHello, rSentAck

vars == <<iPhase, rPhase, msgs, delivered, iSentHello, rSentAck>>

IPhases == {"idle", "handshaking", "established", "closed"}
RPhases == {"idle", "established", "closed"}

TypeOK ==
  /\ iPhase \in IPhases
  /\ rPhase \in RPhases
  /\ msgs \subseteq Message
  /\ delivered \subseteq Message
  /\ iSentHello \in BOOLEAN
  /\ rSentAck \in BOOLEAN

Init ==
  /\ iPhase = "idle"
  /\ rPhase = "idle"
  /\ msgs = {}
  /\ delivered = {}
  /\ iSentHello = FALSE
  /\ rSentAck = FALSE

-----------------------------------------------------------------------------
(* Send: the initiator opens the connection by enqueuing a genuine "hello"
   onto the channel. `iSentHello` is a pure history/ghost flag -- set TRUE
   the instant a real (uncorrupted, not-yet-existing) hello is sent and
   never reset -- exactly like `sawHandshaking` in AntProtocol.tla. It is
   the ground truth NoFalseEstablishment below is checked against. *)
SendHello ==
  /\ iPhase = "idle"
  /\ iPhase' = "handshaking"
  /\ msgs' = msgs \cup {[kind |-> "hello", sender |-> "I"]}
  /\ iSentHello' = TRUE
  /\ UNCHANGED <<rPhase, delivered, rSentAck>>

(* Deliver (responder side): a "hello" sitting in the channel is
   nondeterministically EITHER delivered and processed (transitioning R to
   "established" and producing the real "hello_ack" reply, matching
   `accept_hello`'s single-call phase+reply semantics) OR silently dropped
   -- removed from the channel with no effect, modeling the bus's "drop"
   fault mode via TLC's own nondeterministic choice rather than a
   probability. Either way the message leaves the channel: a dropped
   packet does not sit around to be delivered twice by accident (that is
   what the separate Duplicate action is for). *)
ReceiveHello ==
  \E m \in msgs :
    /\ m.kind = "hello"
    /\ \/ /\ rPhase = "idle"
          /\ rPhase' = "established"
          /\ msgs' = (msgs \ {m}) \cup {[kind |-> "hello_ack", sender |-> "R"]}
          /\ delivered' = delivered \cup {m}
          /\ rSentAck' = TRUE
       \/ /\ msgs' = msgs \ {m}
          /\ UNCHANGED <<rPhase, delivered, rSentAck>>
    /\ UNCHANGED <<iPhase, iSentHello>>

(* Deliver (initiator side): symmetric handling of an in-flight genuine
   "hello_ack" -- either resolves the initiator's pending handshake
   (Handshaking -> Established, matching `HandshakingSession.complete`) or
   is silently dropped. *)
ReceiveAck ==
  \E m \in msgs :
    /\ m.kind = "hello_ack"
    /\ \/ /\ iPhase = "handshaking"
          /\ iPhase' = "established"
          /\ msgs' = msgs \ {m}
          /\ delivered' = delivered \cup {m}
       \/ /\ msgs' = msgs \ {m}
          /\ UNCHANGED <<iPhase, delivered>>
    /\ UNCHANGED <<rPhase, iSentHello, rSentAck>>

(* Corrupt: transforms an in-flight genuine message's kind tag into the
   undecodable "corrupt" tag -- the direct analogue of the real bus's
   `FaultInjector.corrupt()` XOR-ing a wire byte until the receiver's
   `decode` can no longer recognize the frame (`MalformedMessage`, ISC-24).
   Note the message's `sender` field is preserved (corruption mangles the
   wire *content*, not which physical channel/direction it arrived on) but
   its `kind` becomes unrecognizable, so neither ReceiveHello nor
   ReceiveAck can ever match it again. *)
Corrupt ==
  \E m \in msgs :
    /\ m.kind \in {"hello", "hello_ack"}
    /\ msgs' = (msgs \ {m}) \cup {[kind |-> "corrupt", sender |-> m.sender]}
    /\ UNCHANGED <<iPhase, rPhase, delivered, iSentHello, rSentAck>>

(* DeliverCorrupt: a peer attempts to receive an already-corrupted frame
   and, exactly like the real `try_recv` returning `Result.Err
   (MalformedMessage(...))`, the frame is discarded with no phase
   transition and no crash -- the runtime guard mypy --strict cannot
   provide, because the wire boundary is untyped bytes. *)
DeliverCorrupt ==
  \E m \in msgs :
    /\ m.kind = "corrupt"
    /\ msgs' = msgs \ {m}
    /\ UNCHANGED <<iPhase, rPhase, delivered, iSentHello, rSentAck>>

(* Duplicate: re-enqueues a copy of a message that has *already been
   delivered* (i.e. already caused its real phase transition and is
   recorded in `delivered`) -- a replay of a genuine past message, not a
   duplicate-before-first-delivery. This is deliberately the harder/more
   interesting fault to model: it proves that even a perfectly genuine,
   previously-real message replayed back onto the channel cannot force a
   *second*, illegitimate establishment, because ReceiveHello/ReceiveAck's
   phase guards (`rPhase = "idle"` / `iPhase = "handshaking"`) are no
   longer satisfied once the real handshake has already resolved -- the
   replayed copy can only ever be re-consumed via the "drop" disjunct.
   `delivered` itself is never grown by Duplicate (only by a genuine first
   delivery), so replay does not manufacture new "evidence" either. *)
Duplicate ==
  \E m \in delivered :
    /\ msgs' = msgs \cup {m}
    /\ UNCHANGED <<iPhase, rPhase, delivered, iSentHello, rSentAck>>

CloseInitiator ==
  /\ iPhase = "established"
  /\ iPhase' = "closed"
  /\ UNCHANGED <<rPhase, msgs, delivered, iSentHello, rSentAck>>

CloseResponder ==
  /\ rPhase = "established"
  /\ rPhase' = "closed"
  /\ UNCHANGED <<iPhase, msgs, delivered, iSentHello, rSentAck>>

Next ==
  \/ SendHello
  \/ ReceiveHello
  \/ ReceiveAck
  \/ Corrupt
  \/ DeliverCorrupt
  \/ Duplicate
  \/ CloseInitiator
  \/ CloseResponder

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
(* NoFalseEstablishment: the direct TLA+ analogue of what ISC-23/24 test in
   Python -- a peer is never "established" (or having-been-established, via
   "closed", which is only reachable from "established") without the
   corresponding REAL message having genuinely been sent by the other side,
   even under an arbitrary interleaving of drop, duplicate, and corrupt
   faults. `iSentHello`/`rSentAck` are pure ghost history flags that a
   real, non-corrupted send action sets and nothing ever resets, so this
   invariant is checking cross-peer provenance, not merely "a message with
   the right kind currently sits in the channel" (which drop/corrupt could
   make trivially false without saying anything about history). *)
NoFalseEstablishment ==
  /\ (rPhase \in {"established", "closed"}) => iSentHello
  /\ (iPhase \in {"established", "closed"}) => rSentAck

=============================================================================
