# `formal/` — optional Lean 4 + TLA+ side-spec

Project-root directory (`projects/templates/template_formal/formal/`) holding
two independent, non-Python, mathematically-checked models of the same
handshake protocol that `src/template_formal/protocol/session.py` implements
at runtime. The pure domain package is independent of these tools, but the
complete selected test suite includes actual Lean/TLC acceptance controls in
`tests/test_tool_acceptance.py`; they are not decorative files exercised only
by the shell wrapper. Prepare the declared `formal-tools` extra and real pinned
capabilities before claiming that complete suite. Missing capability remains
blocked, never a substituted success. Lean's proof and TLC's finite-model
checks retain their separate guarantees and do not prove universal equivalence
to the Python implementation.

The side-specs live only in this project-root directory. Domain Python remains
under `src/template_formal/`; executable checks belong to the canonical wrapper
and complete-suite controls, not a duplicate decorative specification package.

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

The wrapper requires Python3.14+, elan, a selected Java runtime, and this project's optional
`formal-tools` extra, which includes the declared platform SDK (already supplied by the canonical checkout).
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
