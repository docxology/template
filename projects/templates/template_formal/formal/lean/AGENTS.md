# `formal/lean/` — Agent Guide

Parent layer contract: [`../AGENTS.md`](../AGENTS.md). Repo-wide Lean
conventions: `Skill("lean-proof")`, `Skill("mathlib-review")`,
`Skill("lean4-setup")` (see `~/.claude/PAI/MEMORY/WORK/*goldilocks*` for the
sibling `goldilocks_math` Lean project, if you need a second reference point
for this repo's Lean discipline — it is a separate project, not part of this
template).

## The vacuity trap — read this before adding or editing a theorem

This single file has already hit the **same defect class twice** across two
adversarial review rounds:

1. `no_direct_idle_to_established` originally wrapped its real content
   (there is no `idle -> established` single-step edge) inside a
   `Reaches`-based three-way disjunction that was satisfiable by a fixed
   witness regardless of which run was actually passed in — restating
   `established_requires_handshaking` in weaker clothing, not adding new
   content. Fixed by stating the direct, `Reaches`-free one-step
   non-existence claim instead.
2. A later theorem, `closed_only_via_known_paths`, was found by a *second*,
   independent Forge pass carrying the **identical** near-vacuity shape —
   its conclusion was also satisfiable by a fixed proof term independent of
   the actual hypothesis. It was removed rather than patched a second time
   (see the long docstring above `step_to_closed_cases` in
   `AntProtocol.lean` for the full reasoning) once `step_to_closed_cases`
   was recognized as the actual load-bearing statement.

**The lesson, stated generally** (also recorded in this repo's shared
memory as `gotcha-goodness-of-fit-green-by-construction` and
`gotcha-necessary-condition-is-not-partial-progress-S2-not-S4`): fixing one
instance of a vacuous-theorem defect does not immunize the rest of the file
against the same shape. Before adding a new theorem here, ask: *is this
conclusion true unconditionally, for a fixed witness, regardless of what
hypothesis a caller supplies?* If yes, it is decoration, not a proof of
anything specific to the hypothesis — restate it as the direct, hypothesis-free
claim it actually is (as both fixes above did), or drop it.

## Non-vacuity witnesses are mandatory, not optional polish

`established_reachable`, `closed_reachable_via_established`, and
`closed_reachable_via_abort` exist specifically so that
`established_requires_handshaking`/`closed_is_terminal`/etc. cannot be
vacuously true about relations with no actual inhabitants. Any new safety
theorem of the form `P -> Q` needs a companion witness proving `P` is
actually satisfiable by some real term — otherwise a reviewer (or a future
you) cannot distinguish "this is a real safety fact" from "this implication
is true only because its premise can never hold."

## Editing checklist

1. Never introduce `sorry` or `admit` — `grep -n 'sorry\|admit'
   AntProtocol.lean` must stay empty.
2. Never introduce a project-level `axiom` declaration. If a proof seems to
   need one, that is a sign the theorem statement is wrong, not that an
   axiom is warranted — this file's whole discipline is "checked by Lean's
   own kernel," and mathlib is deliberately not a dependency (`lakefile.lean`
   declares none), so there is no legitimate axiom this file should need
   beyond Lean's own core (`propext`/`Classical.choice`/`Quot.sound`).
3. Every new theorem gets a trailing `#print axioms <name>` line at the
   bottom of the file, in the same block as the existing seven. Run `lake
   build` and read the printed axiom set for the new line — an unexpected
   entry there is the concrete, mechanical check that catches an
   accidentally-introduced axiom; do not skip reading it just because the
   build exited 0.
4. If you touch `Step`, `Reaches`, or `Phase`'s constructors, re-derive
   `phase_exhaustive` and `step_to_closed_cases` by hand first — both are
   written as an explicit case split over the *current* constructor set, so
   adding a constructor without revisiting these two theorems will either
   fail to compile (good, loud) or — worse — silently leave a case unproved
   because you didn't re-run `cases` and let Lean tell you what's missing.
5. Update [`../../manuscript/05_results_discussion.md`](../../manuscript/05_results_discussion.md)
   (§"The optional formal side-spec: shipped, not cut" / §"Formal side-spec
   expansion") and [`README.md`](README.md)'s theorem table if the theorem
   count or claims change — the manuscript quotes "7 theorems total, zero
   `sorry`, zero extra axioms" as a specific, checkable number.

## Build / verify

```bash
export PATH="$HOME/.elan/bin:$PATH"
cd projects/templates/template_formal/formal/lean
lake build
```

Or via the combined wrapper from the project root:
`scripts/check_formal_specs.sh` (runs this build as its first of three checks).

## See also

- [`README.md`](README.md) — theorem table, `SessionToken` affine model, zero-sorry discipline
- [`../AGENTS.md`](../AGENTS.md) — the `formal/` directory's own contract (wiring requirement)
- [`../../scripts/check_formal_specs.sh`](../../scripts/check_formal_specs.sh)
