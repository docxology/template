# Selected child execution

`scripts/realize_archetypes.py` selects one exact grammar cell per permitted
primitive domain. `scripts/realize_child_full.py` selects one of those children,
using the seeded preferred domain when the filters permit it. Both entrypoints
honor `project_config.autopoiesis.archetype_filters`, record exact selected specs,
and exit nonzero when any required producer fails. The default five-child run
does not claim execution of all 45 effective or 360 nominal grammar cells.
Selection rejects unsupported selected primitive domains and caps the declared
nominal grammar product at 10,000 cells before enumeration.

Each child is materialized in a disposable directory under ignored
`output/.pipeline/child_realization/workspaces/`. Its actual standalone domain
tests retain the parent's substantive oracle assertions, changing only the
package import prefix. They run with a 90% coverage gate, followed by actual
numerical analysis. The analysis writes `output/data/analysis_results.json` with
schema `autopoiesis/child-analysis/1`, selected domain, and every primitive result.
The parent independently recomputes the selected kernels and checks the exact
result membership, shape, and declared numerical tolerance.

The shared platform process boundary reaps child descendants, strips host
credentials, and limits each child test or analysis invocation to 60 seconds. The trusted bootstrap also
sets CPU, 16 MiB file-size, and 128-open-file limits. Linux enforces a 1 GiB
address-space limit; macOS records that this limit is unavailable. This executes
trusted generated source. It provides no claim of hostile-code filesystem or
network containment. Child PDF rendering remains explicitly unsupported.
This lane requires platform 4.0.0 from the checkout or an installed platform
package. The supervisor and actual imported generator are admitted before
materialization. Missing or mismatched platform execution is blocked with exit
75 and an empty executed-child set;
pure standalone materialization remains available, with no host supervisor fallback.

The coordinator recomputes the structural honesty manifest from the selected
project's current AST. Receipt schema `autopoiesis/selected-child-execution/2`
keeps three distinct custody records: `source_sha256` binds the supplied project
configuration, source, and scientific reference oracles;
`active_generator_custody` binds the actual imported generator package;
`platform_custody` binds the actual shared supervisor. A source checkout requires
its own matching `pyproject.toml` and `uv.lock`. An installed generator requires
its genuine distribution METADATA, RECORD, exact Python file roster, and file
hashes. No manuscript or checkout markers are inferred inside site-packages.
The manifest checks required operations
inside named functions and rejects named stubs and an empty evidence set.
Structural evidence is accompanied by separate actual execution receipts;
function calls in an AST alone do not establish runtime correctness. Ordinary
execution records a loaded baseline for generator bytecode. Installed acceptance
passes a launcher-owned fresh bytecode prefix and verifies the shared pre-import
audit; only that lane records `fresh-owned-prefix` custody.

Source bytes and recomputed provenance are checked before execution, after
execution, and after export. Before recording success the coordinator recaptures
both imported implementations and the project references and requires exact
agreement. Empty or duplicated file rosters, traversal,
symlink components, missing producers, invalid artifacts, and numerical drift
fail acceptance. Current source, analysis, and coverage exports go to ignored
`output/.pipeline/child_realization/exports/`. Historical published children
under `output/children/` remain unchanged. `04_seal.py` seals only the current
manifest-selected runtime child, with its actual spec hash and recomputed tree
hash; source verification failure prevents writing a seal.

`archetypes.json` or `single.json` in the runtime directory retains the selected
specs, filters, declared-cell count, source hashes, structural manifest, each
producer's command/exit/timeout/output, independent result verdict, and export
hashes. Failed runs retain the available diagnostic receipt. No child artifact
is published by these commands.

`child_process_deadline_sec` bounds each child test invocation and each child
analysis invocation separately. It is not a whole-producer deadline. The parent
pipeline stage has its own supervisory deadline. Five selected children require
ten separately bounded subprocess invocations plus finite materialization and
custody work.

Child supervision separates the whole launch/execution wall deadline from CPU
consumption. `execute_child(..., timeout=60, cpu_seconds=1)` allows the finite
launch boundary to start the child while enforcing one second of actual child
CPU. The CPU budget must be a positive integer within the whole deadline; its
default equals that deadline. A refusal before command launch does not establish
resource-limit acceptance. Pure materialization does not import plotting; public
figure APIs load their original implementation when requested.
