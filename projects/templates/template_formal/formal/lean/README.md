# `formal/lean/` — Lean 4 spec of the handshake protocol

`AntProtocol.lean` is a small, standalone (**no mathlib dependency**) Lean 4
model of the same session-type-shaped phase state machine that
`src/template_formal/protocol/session.py` implements at runtime:

```
Idle -> Handshaking -> Established -> Closed
```

plus two abort edges (`Idle -> Closed`, `Handshaking -> Closed`). It is
deliberately **not** a transliteration of the Python code — it is an
independent mathematical model checked by Lean's own kernel, so a bug in the
Python implementation and a bug in this spec cannot silently agree with each
other.

## What is actually proved (verify this list yourself before trusting it)

The file's own closing lines are the source of truth, not this README —
run `grep -n '#print axioms' AntProtocol.lean` or open the file's last
seven lines directly. As of the current file, seven theorems are proved and
each has a trailing `#print axioms` check:

| Theorem | Claim |
| --- | --- |
| `established_requires_handshaking` | Core safety property: any well-formed run reaching `established` from `idle` passed through `handshaking` — there is no direct `idle -> established` edge in a *run* of arbitrary length. |
| `step_to_closed_cases` | Every single `Step` into `closed` originates from exactly `idle`, `established`, or `handshaking` — an exhaustive case split on the `Step` relation itself. |
| `no_direct_idle_to_established` | There is no single-step edge `idle -> established` (a one-step, not a run-length, non-existence claim). |
| `phase_exhaustive` | `Phase` has exactly four inhabitants — `idle`, `handshaking`, `established`, `closed` — nothing else. |
| `closed_is_terminal` | No legal one-step transition exists out of `closed` in any direction. |
| `session_token_use_succeeds` | Non-vacuity witness: a fresh `SessionToken` can be constructed and consumed once. |
| `cannot_reuse_consumed_token` | The affine-discipline core claim: no well-typed proof term can license consuming an already-consumed `SessionToken` a second time — the precondition a second call would need is provably unsatisfiable. |

Three additional theorems (`established_reachable`,
`closed_reachable_via_established`, `closed_reachable_via_abort`) exist purely
as **non-vacuity witnesses** — proof that `established`/`closed` are actually
reachable at all, so the safety theorems above aren't vacuously true about an
empty relation. They are not part of the `#print axioms` list because they
assert reachability, not an implication that could otherwise be trivially
satisfied.

`SessionToken` models the `_consumed`-flag discipline that
`SessionConsumedError` enforces at runtime in `protocol/session.py`
(`IdleSession.open`, `.accept_hello`, `HandshakingSession.complete`,
`EstablishedSession.close`) — as a plain Lean `structure` with a `used : Bool`
field, since this file is mathlib-free and has no algebraic linear/affine
type machinery available. The precondition on `SessionToken.use` is the
type-level analogue of the Python's `if self._consumed: raise ...` guard.

## Zero `sorry`, zero extra axioms

This is a hard discipline, not a slogan: `grep -n 'sorry\|admit' AntProtocol.lean`
must return nothing, and every `#print axioms` line at the bottom of the file
must report only Lean's own core axioms (`propext`, `Classical.choice`,
`Quot.sound` — whichever subset the specific proof actually needs), never a
project-introduced `axiom` declaration. A theorem proved via `sorry` type-checks
but proves nothing; a hidden extra `axiom` can make a false statement provable.
Neither exists in this file — confirm with `lake build` (below) plus reading
the seven `#print axioms` outputs.

## Build

```bash
export PATH="$HOME/.elan/bin:$PATH"   # if using elan (recommended)
cd projects/templates/template_formal/formal/lean
lake build
```

Pinned toolchain: `leanprover/lean4:v4.28.0` (`lean-toolchain`). The
`lakefile.lean` declares a minimal package (`ant_protocol`) with a single
`lean_lib` target (`AntProtocol`) and zero external dependencies — `lake
build` does not fetch mathlib or anything else, so it stays fast (single
small file).

A successful build prints something like `Build completed successfully` and
exit 0; the seven `#print axioms` lines print alongside the build output —
inspect them directly rather than trusting a bare exit code, since a
`#print axioms` line reporting an unexpected project-introduced axiom would
still leave the build exit-0.

To run the checked-out `.olean`/build cache from scratch (e.g. after a
toolchain bump), `rm -rf .lake && lake build`.

## See also

- [`AGENTS.md`](AGENTS.md) — editing rules, the vacuity trap this file already hit twice
- [`../README.md`](../README.md) — why this spec sits beside a separate TLA+ model rather than replacing it
- [`../../scripts/check_formal_specs.sh`](../../scripts/check_formal_specs.sh) — runs `lake build` as one leg of the combined formal check
- [`../../src/template_formal/protocol/session.py`](../../src/template_formal/protocol/session.py) — the runtime implementation this spec mirrors (independently, not by transliteration)
