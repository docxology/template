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

## Running all checks

From the project root, select a real Java runtime and run the canonical wrapper:

```bash
FORMAL_JAVA_BIN=/opt/homebrew/opt/openjdk/bin/java scripts/check_formal_specs.sh --timeout 300
# Explicit first acquisition of the exact pins:
FORMAL_JAVA_BIN=/opt/homebrew/opt/openjdk/bin/java scripts/check_formal_specs.sh --acquire --timeout 300
# Optional ignored execution receipt:
scripts/check_formal_specs.sh --receipt output/.pipeline/formal_tools/receipt.json
```

The wrapper requires Python3.12+, elan, a selected Java runtime, and the optional
`formal-tools` platform4.0.1 extra (already supplied by the canonical checkout).
Its filesystem main uses a private fresh cache before platform imports. The
supervised tool worker additionally uses the platform's pre-import executed-code
audit; the controller is not claimed to have that audit. Timestamp-valid
ordinary caches cannot authorize that worker. The
domain package remains standalone; absence of the optional platform blocks75.
Set
`FORMAL_PYTHON_BIN` when the project interpreter is not `python3` on PATH and
`FORMAL_JAVA_BIN` when Java is elsewhere. It never silently upgrades the declared
Lean4.35.0 toolchain or dependency-free manifest. Acquisition admits only the
exact TLC release bytes declared in `template_formal.tool_acceptance`.

Fresh Lean elaboration must produce all seven clean axiom audits. Both positive
TLC models must complete, and the negative control must produce its specific
invariant violation with exit12. Held no-follow descriptors admit bounded
regular source files, refusing links and FIFOs before reading them. Lean and
TLC consume private read-only copies of those exact admitted declarations and
model/configuration bytes; each executed check records its consumed source
hashes. Lake builds use a fresh private cache. One total wall-clock deadline
bounds source admission, every child, acquisition, cleanup and final custody.
Missing tools are blocked75; invalid declarations exit2,
failures1, and timeouts124. Actual sources/pins must remain unchanged. These
finite-model results do not prove universal Python implementation equivalence.

## See also

- [`lean/README.md`](lean/README.md), [`lean/AGENTS.md`](lean/AGENTS.md) — the Lean 4 spec
- [`tla/README.md`](tla/README.md), [`tla/AGENTS.md`](tla/AGENTS.md) — the two TLA+ specs
- [`../AGENTS.md`](../AGENTS.md) — project layer contract (`formal/` row)
- [`../manuscript/05_results_discussion.md`](../manuscript/05_results_discussion.md) — §"The optional formal side-spec: shipped, not cut" and §"Formal side-spec expansion: what grew, and what still needs wiring"
- [`../scripts/check_formal_specs.sh`](../scripts/check_formal_specs.sh) — the wiring script itself, fully commented
