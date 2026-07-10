--------------------- MODULE AntProtocolFaultyNegControl ---------------------
(* NEGATIVE CONTROL / proof-of-detection for AntProtocolFaulty.tla's
   NoFalseEstablishment invariant.

   This module is DELIBERATELY BROKEN. It exists to be REJECTED by TLC, and
   `scripts/check_formal_specs.sh` asserts TLC reports an invariant
   violation here (a non-zero exit) -- the TLA+ analogue of the mypy-oracle
   `bad_*.py` fixtures under `tests/mypy_fixtures/`, which prove a
   `mypy --strict` gate is not vacuous by exhibiting code it actually
   rejects. Without a negative control, "TLC checked NoFalseEstablishment
   and found no violation" says nothing about whether the invariant CAN
   detect the vulnerability class it advertises: a tautologically-true or
   guard-independent invariant would also report "no violation."

   WHY THIS PARTICULAR MUTATION (and not the tempting one).
   ---------------------------------------------------------
   NoFalseEstablishment is `rPhase \in {established,closed} => iSentHello`
   (and the symmetric ack clause). `iSentHello`/`rSentAck` are pure
   send-side history flags: SendHello sets `iSentHello` the instant a
   GENUINE hello is created, ReceiveHello's accept branch sets `rSentAck`,
   and nothing ever resets them. The invariant therefore certifies
   send-PROVENANCE ("a real message was genuinely sent by the other peer"),
   NOT content-integrity ("the specific delivered frame was uncorrupted").

   A naive negative control -- widening ReceiveHello's guard from
   `m.kind = "hello"` to also accept a "corrupt" frame -- does NOT violate
   NoFalseEstablishment, precisely because `Corrupt` preserves a message's
   `sender` field and only ever acts on a message that a genuine SendHello
   already put on the channel (which already set `iSentHello = TRUE`). So
   accepting a corrupted-but-genuinely-originated frame still satisfies the
   provenance invariant. That mutation is reachable (it enlarges the state
   space) yet the invariant stays green -- which is exactly the point: the
   invariant is INSENSITIVE to content corruption by design, and any
   manuscript claim must say "send-provenance," not "content-integrity
   resilience."

   To exhibit a real violation we must instead break send-PROVENANCE: below,
   `ForgeHello` injects a `[kind |-> "hello", sender |-> "I"]` message onto
   the channel WITHOUT setting `iSentHello` -- an unauthenticated / spoofed
   hello that was never genuinely sent by the initiator. The unmodified
   ReceiveHello then delivers it, driving `rPhase` to "established" while
   `iSentHello` is still FALSE, so `rPhase = established => iSentHello` is
   violated. TLC finds this in a short trace:
   Init -> ForgeHello -> ReceiveHello(accept). This proves
   NoFalseEstablishment genuinely depends on provenance holding, rather than
   being green-by-construction.

   Every other action, variable, and the NoFalseEstablishment invariant
   itself are copied VERBATIM from AntProtocolFaulty.tla; the ONLY change is
   the added ForgeHello action and its inclusion in Next. *)

EXTENDS Naturals, FiniteSets

Senders == {"I", "R"}
Kinds == {"hello", "hello_ack", "corrupt"}

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
SendHello ==
  /\ iPhase = "idle"
  /\ iPhase' = "handshaking"
  /\ msgs' = msgs \cup {[kind |-> "hello", sender |-> "I"]}
  /\ iSentHello' = TRUE
  /\ UNCHANGED <<rPhase, delivered, rSentAck>>

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

Corrupt ==
  \E m \in msgs :
    /\ m.kind \in {"hello", "hello_ack"}
    /\ msgs' = (msgs \ {m}) \cup {[kind |-> "corrupt", sender |-> m.sender]}
    /\ UNCHANGED <<iPhase, rPhase, delivered, iSentHello, rSentAck>>

DeliverCorrupt ==
  \E m \in msgs :
    /\ m.kind = "corrupt"
    /\ msgs' = msgs \ {m}
    /\ UNCHANGED <<iPhase, rPhase, delivered, iSentHello, rSentAck>>

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

(* THE INJECTED DEFECT: a forged/unauthenticated hello enters the channel
   with NO corresponding genuine send -- `iSentHello` is left untouched
   (FALSE until some genuine SendHello runs). This is the send-provenance
   violation NoFalseEstablishment is supposed to catch. *)
ForgeHello ==
  /\ msgs' = msgs \cup {[kind |-> "hello", sender |-> "I"]}
  /\ UNCHANGED <<iPhase, rPhase, delivered, iSentHello, rSentAck>>

Next ==
  \/ SendHello
  \/ ReceiveHello
  \/ ReceiveAck
  \/ Corrupt
  \/ DeliverCorrupt
  \/ Duplicate
  \/ CloseInitiator
  \/ CloseResponder
  \/ ForgeHello

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
NoFalseEstablishment ==
  /\ (rPhase \in {"established", "closed"}) => iSentHello
  /\ (iPhase \in {"established", "closed"}) => rSentAck

=============================================================================
