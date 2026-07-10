---------------------------- MODULE AntProtocol ----------------------------
(* Minimal TLA+ model of the same ant-robot handshake protocol modeled in
   AntProtocol.lean: a single connection's phase state machine

     Idle -> Handshaking -> Established -> Closed

   with two abort edges (Idle -> Closed, Handshaking -> Closed) mirroring the
   Lean `Step` relation exactly (open_, ack, closeEst, abortIdle, abortHs).

   This is a state-machine-level model (single agent-pair connection), not a
   distributed multi-process spec -- matching the ISA's Out of Scope: no
   real sockets, no consensus protocol. TLC explores every reachable state
   of (phase, sawHandshaking) and checks the invariants below. *)

EXTENDS Naturals, FiniteSets

Phases == {"idle", "handshaking", "established", "closed"}

VARIABLES phase, sawHandshaking

vars == <<phase, sawHandshaking>>

TypeOK == phase \in Phases /\ sawHandshaking \in BOOLEAN

Init == phase = "idle" /\ sawHandshaking = FALSE

(* Legal one-step transitions, mirroring Lean's `Step` constructors exactly.
   `sawHandshaking` is a pure history/ghost variable: it is set TRUE the
   instant the machine enters "handshaking" and never reset, so it records
   "has this run ever visited handshaking so far." It does not influence
   which transitions are enabled. *)
Open ==
  /\ phase = "idle"
  /\ phase' = "handshaking"
  /\ sawHandshaking' = TRUE

Ack ==
  /\ phase = "handshaking"
  /\ phase' = "established"
  /\ sawHandshaking' = sawHandshaking

CloseEst ==
  /\ phase = "established"
  /\ phase' = "closed"
  /\ sawHandshaking' = sawHandshaking

AbortIdle ==
  /\ phase = "idle"
  /\ phase' = "closed"
  /\ sawHandshaking' = sawHandshaking

AbortHs ==
  /\ phase = "handshaking"
  /\ phase' = "closed"
  /\ sawHandshaking' = sawHandshaking

(* Once closed, the connection is terminal -- no outgoing edges from
   "closed"; TLC permits stuttering there under the standard
   [Next]_vars convention below. *)
Next == Open \/ Ack \/ CloseEst \/ AbortIdle \/ AbortHs

(* Weak fairness on the two actions that *resolve* a pending handshake
   (Ack: handshaking -> established; AbortHs: handshaking -> closed). Without
   fairness, TLC's exists-a-behavior semantics permits a "coward" run that
   sits in "handshaking" forever by always choosing the (also-enabled)
   stuttering step, which would make any liveness property about handshake
   resolution vacuously unprovable. WF_vars(A) says: if A is continuously
   enabled, it must eventually be taken. Both Ack and AbortHs are enabled by
   the single guard `phase = "handshaking"`, so either one alone would
   already force progress out of "handshaking" -- both are included because
   that is the literal, honest statement of "some resolving action is not
   permanently starved," not because the property strictly needs both. No
   fairness is placed on Open/AbortIdle/CloseEst: HandshakeEventuallyResolves
   below only makes a promise about the "handshaking" phase, so only the
   actions that leave that phase need to be assumed non-starved. *)
Spec == Init /\ [][Next]_vars /\ WF_vars(Ack) /\ WF_vars(AbortHs)

-----------------------------------------------------------------------------
(* Safety invariant #1: the machine is always in one of the four declared
   phases with a boolean ghost flag -- basic well-formedness. *)
SafetyInvariant == TypeOK

(* Safety invariant #2, the real content, mirroring the Lean theorem
   `established_requires_handshaking`: whenever the machine is in
   "established", it must have passed through "handshaking" to get there.
   Because `Ack` is the *only* transition whose target is "established",
   and `Ack` requires the source phase to already be "handshaking" (which
   is exactly when `sawHandshaking` becomes/stays TRUE), this invariant
   holding across every state TLC enumerates is a genuine, non-vacuous
   cross-check of the same safety property proved in Lean -- established
   is never reached directly from idle or by skipping handshaking. *)
EstablishedRequiresHandshaking ==
  (phase = "established") => sawHandshaking

(* Liveness property: once a handshake is pending, it does not stall
   forever -- it is eventually either completed (established) or abandoned
   (closed). This is the temporal counterpart to the safety invariants
   above: safety says "nothing bad happens along the way," liveness says
   "something good (resolution) eventually does." It only holds relative to
   the fairness conjuncts on Spec above -- checked directly against TLC's
   PROPERTIES mechanism, which evaluates the property over the fair
   behaviors of Spec, not merely over the raw next-state relation. *)
HandshakeEventuallyResolves ==
  [](phase = "handshaking" => <>(phase \in {"established", "closed"}))

=============================================================================
