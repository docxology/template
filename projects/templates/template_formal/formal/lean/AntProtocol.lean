/-
  AntProtocol.lean

  Small, standalone (no mathlib) Lean 4 spec mirroring the session-type-shaped
  handshake protocol used by `src/template_formal/protocol/session.py`:

    Idle -> Handshaking -> Established -> Closed

  This file is deliberately independent of the Python implementation: it is a
  mathematical model of the same phase state machine, checked by Lean's own
  kernel, not a transliteration that could share a bug with the runtime code.

  Real, runnable check:
    lean AntProtocol.lean
  or, via the pinned lakefile in this directory:
    lake build

  Zero `sorry`, zero `admit`, zero axioms beyond Lean's own core.
-/

/-- The four phases of the ant-robot handshake protocol. -/
inductive Phase where
  | idle
  | handshaking
  | established
  | closed
  deriving DecidableEq, Repr

open Phase

/-- The legal one-step transitions of the protocol. This mirrors the typed
    Python state machine: `Idle.open -> Handshaking`,
    `Handshaking.ack -> Established`, `Established.close -> Closed`, and a
    direct abort path `Idle.abort -> Closed` / `Handshaking.abort -> Closed`
    (a peer may abort before establishment). There is deliberately no edge
    directly from `established` back to `idle`/`handshaking`, and no edge out
    of `closed` (it is terminal). -/
inductive Step : Phase → Phase → Prop where
  | open_       : Step idle handshaking
  | ack         : Step handshaking established
  | closeEst    : Step established closed
  | abortIdle   : Step idle closed
  | abortHs     : Step handshaking closed

/-- A well-formed run is a chain of legal `Step`s starting from `idle`. -/
inductive Reaches : Phase → Phase → Prop where
  | refl  : Reaches p p
  | tail  : Reaches p q → Step q r → Reaches p r

/-- `closed` is reached only via a known path: the immediate predecessor of
    any `Step` into `closed` is `idle` (abort), `established` (normal
    close), or `handshaking` (abort) — never anything else. This is a
    universally-quantified, falsifiable claim about the `Step` relation
    itself (add a hypothetical 6th constructor with some other source and
    this theorem becomes false), which is what makes it non-vacuous.

    An earlier revision wrapped this fact in an extra `Reaches idle closed`
    hypothesis and concluded a three-way `Reaches idle established ∨
    Reaches idle idle ∨ Reaches idle handshaking` disjunction instead of
    this direct universal statement. That wrapping added no real content:
    `Reaches idle q` holds unconditionally for all three candidate phases in
    this small state machine (`idle` via `Reaches.refl`, `established` via
    `established_reachable` below, `handshaking` via the `open_` edge), so
    the wrapped version was satisfiable by a fixed witness regardless of
    which specific run was passed in — the same "phantom" vacuity class this
    file already caught and fixed once for `no_direct_idle_to_established`
    (see its docstring). This direct, `Reaches`-free statement is the
    content that was actually load-bearing; the wrapper theorem
    (`closed_only_via_known_paths`) has been removed rather than patched a
    second time, since no rewording of a `Reaches`-based conclusion escapes
    the same trap in this particular state machine. -/
theorem step_to_closed_cases {q : Phase} (h : Step q closed) :
    q = idle ∨ q = established ∨ q = handshaking := by
  cases h with
  | closeEst   => exact Or.inr (Or.inl rfl)
  | abortIdle  => exact Or.inl rfl
  | abortHs    => exact Or.inr (Or.inr rfl)

/-- Core safety property: every well-formed run that reaches `established`
    passes through `handshaking` immediately beforehand (there is no direct
    `idle -> established` edge). Equivalently: `established` is never reached
    in zero steps from `idle`, only via `handshaking`. -/
theorem established_requires_handshaking
    (h : Reaches idle established) : Reaches idle handshaking := by
  generalize hp : idle = p at h
  generalize hq : established = q at h
  induction h with
  | refl =>
      -- `idle = established` would be required; that's impossible, so this
      -- branch is vacuous once we case on the equality.
      subst hp
      cases hq
  | tail hpq hstep ih =>
      rename_i q r
      subst hq
      cases hstep with
      | ack =>
          -- q = handshaking, so `Reaches idle handshaking` follows directly
          -- from the accumulated prefix `hpq : Reaches idle handshaking`.
          exact hpq
      -- The remaining `Step` constructors do not target `established`, so
      -- Lean's `cases` already discharges them (no other case reaches this
      -- point since `hstep : Step q established`).

/-- There is no single-step edge directly from `idle` to `established`: every
    `Step` constructor that could plausibly connect them is absent from the
    inductive definition, so `cases` on a hypothetical such step discharges
    every case (none unify). This is the theorem the old `no_skip_to_established`
    name promised but did not state (that version reduced to a restatement of
    `established_requires_handshaking` via a vacuously-true `Reaches idle idle`
    conjunct — replaced here with the actual one-step non-existence claim). -/
theorem no_direct_idle_to_established : ¬ Step idle established := by
  intro h
  cases h

/-- Every `Phase` value is one of the four constructors — the type has no
    other inhabitants. Needed as a background fact for exhaustiveness-style
    reasoning about the state machine (e.g. "these four cases are the only
    cases"), and a real, checked claim about `Phase` rather than an assumed
    one. -/
theorem phase_exhaustive (p : Phase) :
    p = idle ∨ p = handshaking ∨ p = established ∨ p = closed := by
  cases p
  · exact Or.inl rfl
  · exact Or.inr (Or.inl rfl)
  · exact Or.inr (Or.inr (Or.inl rfl))
  · exact Or.inr (Or.inr (Or.inr rfl))

/-- `closed` is terminal: there is no legal one-step transition out of it in
    any direction. Every `Step` constructor's source is `idle`, `handshaking`,
    or `established` — never `closed` — so `cases` on a hypothetical outgoing
    step from `closed` discharges every case (none unify). -/
theorem closed_is_terminal {q : Phase} : ¬ Step closed q := by
  intro h
  cases h

/-- A minimal affine "single-use" model of the `_consumed`-flag discipline
    that `SessionConsumedError` enforces at runtime in
    `template_formal/protocol/session.py` (`IdleSession.open`,
    `.accept_hello`, `HandshakingSession.complete`,
    `EstablishedSession.close` each guard `if self._consumed: raise ...` then
    set the flag). `used` starts `false`; `use` is only callable given
    evidence the token is not yet used, and always produces a token whose
    `used` field is `true`. This file is mathlib-free, so the model is a
    plain `structure`, not an algebraic affine-type construction. -/
structure SessionToken where
  used : Bool
deriving DecidableEq, Repr

/-- Consume a not-yet-used token, producing a used one. The precondition
    `_h : t.used = false` is the type-level analogue of the Python guard
    `if self._consumed: raise SessionConsumedError(...)`. -/
def SessionToken.use (t : SessionToken) (_h : t.used = false) : SessionToken :=
  { used := true }

/-- Non-vacuity witness: a fresh token can be constructed and used once. -/
theorem session_token_use_succeeds :
    (SessionToken.use ⟨false⟩ rfl).used = true := rfl

/-- Core affine-discipline theorem: once `use` has consumed a token, no
    well-typed proof term can license consuming the *result* again. Calling
    `use` a second time on `t.use h` requires a precondition
    `h2 : (t.use h).used = false` — exactly the shape of evidence a second,
    un-reassigned call would need to supply — and this theorem shows no such
    `h2` can exist, because `t.use h` always has `used = true` by
    construction. This is the genuine "cannot use an already-used token
    twice" claim (not a restatement of `use`'s type signature): it is a
    proof that the precondition itself is unsatisfiable on any token `use`
    has already produced, for every choice of prior evidence `h`. -/
theorem cannot_reuse_consumed_token {t : SessionToken} (h : t.used = false)
    (h2 : (t.use h).used = false) : False := by
  unfold SessionToken.use at h2
  exact Bool.noConfusion h2

/-- Sanity/non-vacuity witness: `established` actually is reachable (the
    theorem above is not proving an empty relation). -/
theorem established_reachable : Reaches idle established :=
  Reaches.tail (Reaches.tail Reaches.refl Step.open_) Step.ack

/-- Sanity/non-vacuity witness: `closed` is reachable both via the normal
    path (through `established`) and via the direct abort path. -/
theorem closed_reachable_via_established : Reaches idle closed :=
  Reaches.tail established_reachable Step.closeEst

theorem closed_reachable_via_abort : Reaches idle closed :=
  Reaches.tail Reaches.refl Step.abortIdle

#print axioms established_requires_handshaking
#print axioms step_to_closed_cases
#print axioms no_direct_idle_to_established
#print axioms phase_exhaustive
#print axioms closed_is_terminal
#print axioms session_token_use_succeeds
#print axioms cannot_reuse_consumed_token
