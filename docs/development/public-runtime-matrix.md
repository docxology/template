# Public runtime acceptance matrix

The strict matrix in `scripts/gates/public_readiness.py --acceptance-matrix`
executes every canonical public exemplar on every supported Python minor.
`PUBLIC_PROJECT_NAMES`, `CANONICAL_CI_PYTHON_VERSIONS`, and each project's
source-owned required acceptance profile determine the product. The current
product is the canonical public roster on Python 3.14 and 3.15; its exact
cell count is derived from those source-owned declarations.

Select already installed interpreters and dedicated dependency environments.
The runner never acquires Python or installs packages. Explicit setup is separate
from acceptance execution. An offline setup example for each installed minor is:

```bash
UV_PROJECT_ENVIRONMENT=/tmp/platform-test-envs/3.14 \
  uv sync --locked --offline --group active-inference --python 3.14 --no-python-downloads
UV_PROJECT_ENVIRONMENT=/tmp/platform-test-envs/3.15 \
  uv sync --locked --offline --group active-inference --python 3.15 --no-python-downloads

export P4_PYTHON314=/tmp/platform-test-envs/3.14/bin/python
export P4_PYTHON315=/tmp/platform-test-envs/3.15/bin/python
```

If an installed interpreter or cached locked dependency is absent, setup refuses;
prepare it explicitly before starting the matrix. These commands leave the
checkout's shared `.venv` and lockfile intact.

Advanced Literature Review consumes the genuine namespaced Meta engine
distribution. Root dependency setup alone does not install that public provider.
First obtain an admitted current wheel from the
[`installed-wheel runner`](installed-wheel-matrix.md), then set
`P4_INSTALLED_RECEIPT` to its actual retained `receipt.json` below this checkout's
`output/readiness`. A diagnostic provider-only installed run may prepare that
wheel, but does not establish complete installed-matrix acceptance. This command
selects an actual successful provider observation and checks its retained bytes;
it does not invent a wheel or an acceptance receipt:

```bash
: "${P4_INSTALLED_RECEIPT:?Set to an actual installed-run receipt.json}"
P4_META_PROVIDER_WHEEL=$(
  uv run --no-sync --offline python - "$P4_INSTALLED_RECEIPT" <<'PY'
import sys
from pathlib import Path
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

root = Path.cwd()
reader = SnapshotReader(root)
receipt = reader.read(Path(sys.argv[1]).absolute().relative_to(root).as_posix()).json_object()
scope = "templates/template_literature_meta_analysis"
observations = [
    row for row in receipt["installed_matrix"]["results"]
    if row["scope"] == scope and row["python_version"] == "3.14"
]
if (receipt["installed_matrix"]["source_current"] is not True
        or len(observations) != 1 or observations[0]["status"] != "pass"):
    raise SystemExit("A successful source-current Meta provider observation is required")
artifact = observations[0]["details"]["wheel_artifact"]
wheel = reader.read(artifact["path"])
if wheel.sha256 != artifact["sha256"]:
    raise SystemExit("The retained provider wheel differs from its actual observation")
print(root / wheel.relative)
PY
)
export P4_META_PROVIDER_WHEEL

for interpreter in "$P4_PYTHON312" "$P4_PYTHON313" "$P4_PYTHON314"; do
  uv pip install --offline --no-config --no-deps --reinstall \
    --python "$interpreter" "$P4_META_PROVIDER_WHEEL"
done
```

Install the wheel into each prepared environment during explicit setup. Runtime
admission binds the provider's current canonical source, declared distribution
and version, wheel contents, actual installed METADATA/RECORD, and consumed
package bytes. An editable Meta source tree or an unrelated installed package
cannot satisfy this contract. Any source or provider change requires a new
admitted wheel and refreshed installations.

Run the complete acceptance matrix with the prepared environments and actual
provider wheel:

```bash
uv run --no-sync --offline python scripts/gates/public_readiness.py \
  --acceptance-matrix --project-workers 1 --timeout 7200 --test-timeout 120 \
  --python "3.14=$P4_PYTHON314" \
  --python "3.15=$P4_PYTHON315" \
  --provider-wheel "templates/template_literature_meta_analysis=$P4_META_PROVIDER_WHEEL"
```

Use a fresh `--evidence-dir` below `output/readiness` to choose a named run;
otherwise the runner creates a UUID directory there. All evidence stays in
ignored local output. `--project templates/template_code_project` is a
diagnostic subset and records `matrix_complete: false`.

The default diagnostic command without `--acceptance-matrix`, including
`--profile release --json`, does not produce the required whole-selection,
three-runtime receipts. Do not use it to close the runtime-matrix backlog.

The existing `ProjectTestTask` matrix supplies credential-free supervised
children with finite deadlines. At most three projects run concurrently.
Runtime waves are sequential and each cell holds the canonical project output
lock. The default item deadline is 120 seconds; explicitly declared per-test
deadlines retain their meaning. Collection has a 600-second ceiling within
the overall cell budget. Nested commands inherit the selected environment,
offline/no-sync policy, and process custody.

Each worker, independent collection, and test chunk creates a fresh private
bytecode prefix before importing platform/project source. Existing `.pyc` files
outside source fingerprints cannot substitute for the source being measured.

Each cell performs independent full collection and real pytest execution.
Inherited pytest selection and project `addopts` are cleared. No producer-side
marker exclusion is allowed. Empty collection, collection errors, omitted or
duplicate cases, deselection, skips, setup/teardown errors, failing cases, and
deadline expiry refuse whole-selection acceptance. Live and long-running
unpaid cases remain visible. There is no inferred paid-test exclusion: adding
a paid test would require an explicit source-owned optional-selection contract.

Stateful suites can declare a pure `module:callable` in
`[tool.template].acceptance_test_groups`. The callable must belong to that
project's `src/`, return labeled nonempty pytest selector lists, and partition
the independent collection exactly once. Active Inference reuses its existing
validated coverage-group planner. This path executes tests and does not invoke
its manuscript refresh generators.

The raw files include the actual interpreter probe and binary digest, installed
test-stack versions, complete node IDs and terminal case outcomes, JUnit XML,
supervised child commands/exits, and branch coverage JSON. Owned benchmark and
coverage scratch files stay in the cell's evidence directory. The parent
independently checks receipt nonces, exact collection union, child exits,
supported runtime, the complete measured own-source map, and the 90 percent
project branch-coverage floor.

Project source and stable deliverable identities must match before and after
each cell. The complete public source/deliverable fingerprint must still match
at the end of the matrix. Concurrent changes invalidate the run; schedule a
stable source window for authoritative evidence. Missing selected interpreters
or required test-stack packages produce named `blocked` gates. Execution and
collection failures produce `fail` gates.

The top receipt uses `template-release-readiness-receipt-v2`; runtime and
coverage gate artifacts use `template-required-acceptance-v1`. The matrix
emits only the gates it actually executes. Installed-wheel, pipeline, native
format, domain, live-provider, export, sandbox transfer, and publication gates
remain independent requirements. A successful test matrix alone does not
establish candidate readiness or authorize production publication.

## Root runtime scope

`python -m infrastructure.project.public_acceptance_root` uses the same
original-spec SHA, nonce, supervised child, whole-case union, and independent
reader contracts for the platform root. Supply prepared interpreters with
repeated `--python MINOR=/absolute/env/bin/python`; acquisition is disabled.
Root cells run serially. The canonical 25-project roster requires both supported minors (50 exemplar cells); that required product is not an execution result.

Root scope means the actual repository root, not `projects/root`. Its owned
Python census covers infrastructure, scripts, tests, and exact root Python
files, including root `conftest.py`. Source identity binds the full public
source fingerprint and all 25 stable public deliverable identities. Root branch
coverage measures infrastructure with a 60 percent floor. The existing
`root:coverage` requirement is explicitly bound to `.python-version` (3.14);
the three supported root runtime requirements remain separate.

The production Root policy and prerequisites are now declared under
`infrastructure/config/root-case-policy.json` and
`infrastructure/config/root-case-prerequisites.json`. The coordinator compares
its original complete collection against the reviewed literal family members
before execution. Source-owned classifications retain core, unpaid live,
platform and provider obligations; recognized optional cases require their exact
reviewed reason. Unexpected skips, deselections, failed cases and incomplete
unions still refuse acceptance.

Use `--mode live` for the complete release observation after preparing every
source-declared prerequisite. Core mode retains the unmet live requirements as
blocked release cells. The policy and its fixture controls establish the
execution contract; the actual production Root observations on Python
3.14/3.15 and Darwin/Linux must pass independently. See
[`root-runtime-v2.md`](root-runtime-v2.md) for case custody, branch coverage,
provider admission and transported-host evidence. Installed, portable, native,
hosted and release requirements remain separate gates.
