# `formal/` — optional Lean 4 + TLA+ side-spec

Project-root directory (`projects/templates/template_formal/formal/`) holding
two independent, non-Python, mathematically-checked models of the same
handshake protocol that `src/template_formal/protocol/session.py` implements
at runtime. Neither is required to build, test, or render this exemplar —
`pytest`, `mypy --strict`, and the manuscript pipeline never touch this
directory. It exists to back one specific claim in the manuscript
(`05_results_discussion.md` §"The optional formal side-spec: shipped, not
cut"): that a static-typing exemplar can also show what a *proof assistant*
and a *model checker* — not just `mypy` — establish about the same protocol,
and be honest about where each one's guarantee actually stops.

**This is the only `formal/` directory in the project.** An earlier
`src/template_formal/formal/` package stub existed at one point but was never
imported by any module, test, or script — dead weight sitting inside the
typed `src/` surface that `ISC-36` (`## Verification` in `ISA.md`) exists
specifically to forbid ("no vestigial/unwired formal-spec file exists in the
shipped tree"). It was found and deleted this session; `find
src/template_formal -mindepth 1 -type d -iname 'formal'` now returns nothing
(note: `find src -type d -iname '*formal*'` is **not** the right check here —
it also matches `src/template_formal` itself, since that directory name
contains the substring "formal"). If you ever see a nested `formal/`
directory under `src/template_formal/` again, that is a regression — the
side-spec belongs only here, at the project root, wired to
`scripts/check_formal_specs.sh`.

## Layout

```
formal/
├── lean/   # Lean 4: single-peer protocol + affine-token model, kernel-checked
└── tla/    # TLA+: single-peer (ideal) + two-peer (fault-injected) models, TLC-checked
```

See [`lean/README.md`](lean/README.md) and [`tla/README.md`](tla/README.md)
for what each side actually proves/checks.

## Why two formalisms, not one

The user's own answer during BUILD (`ISA.md` decision log,
2026-07-08T23:00:00Z) was "yes for all" on a single-select question offering
Lean *or* TLA+ — read as a deliberate override toward maximal inclusion, not
an accident. The two are not redundant: Lean proves properties of the *ideal*
single-connection state machine by kernel-checked deduction (a proof term
exists or it doesn't); TLA+'s TLC exhaustively enumerates the *reachable
state space* of both the ideal model and a second, genuinely harder model —
a two-peer protocol with an explicit, fault-injectable message channel
(`AntProtocolFaulty.tla`) mirroring `network/bus.py`'s drop/duplicate/corrupt
fault modes. Lean has no counterpart to that fault-injected model; TLA+ has
no counterpart to Lean's affine-token reuse proof. Each formalism checks what
it is actually good at.

## Running both checks

```bash
scripts/check_formal_specs.sh
```

is the one real, runnable command that wires all three checks (Lean build +
both TLA+ specs) into a single pass/fail exit code — see its own header
comment for the exact requirements and
[`AGENTS.md`](AGENTS.md) below for what each of the three sub-checks does and
why the script is structured the way it is. Both toolchains are **optional
and non-default**: neither `lake`/`elan` nor a Java runtime is a dependency of
the core pipeline, `pytest`, or CI's default job matrix. Install them only if
you want to re-run the formal side yourself:

- **Lean 4 / `lake`**: via [elan](https://github.com/leanprover/elan) — `export PATH="$HOME/.elan/bin:$PATH"`. Pins to `leanprover/lean4:v4.28.0` (`formal/lean/lean-toolchain`); `lake build` will fetch that toolchain on first run if elan is installed.
- **Java runtime for TLC**: any recent JDK (e.g. `/opt/homebrew/opt/openjdk@17/bin/java` on macOS via Homebrew); override the binary path with `FORMAL_JAVA_BIN` if it isn't on `PATH`.

## See also

- [`lean/README.md`](lean/README.md), [`lean/AGENTS.md`](lean/AGENTS.md) — the Lean 4 spec
- [`tla/README.md`](tla/README.md), [`tla/AGENTS.md`](tla/AGENTS.md) — the two TLA+ specs
- [`../AGENTS.md`](../AGENTS.md) — project layer contract (`formal/` row)
- [`../manuscript/05_results_discussion.md`](../manuscript/05_results_discussion.md) — §"The optional formal side-spec: shipped, not cut" and §"Formal side-spec expansion: what grew, and what still needs wiring"
- [`../scripts/check_formal_specs.sh`](../scripts/check_formal_specs.sh) — the wiring script itself, fully commented
