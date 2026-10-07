# Auxiliary acceptance execution

Run selected checks with the nominated environment, a fresh evidence directory,
and one total deadline:

```bash
python -m infrastructure.project.public_acceptance_auxiliary_cli \
  --gate root:docs_lint --gate root:methods --gate root:macos:process \
  --gate root:macos:rendering --timeout-seconds 600
```

The controller records actual child argv, executable hash, original exit,
timeout, host, stdout/stderr hashes, and public source fingerprints before and
after execution. Each passing result binds independently readable child facts.
Root controls execute invalid inputs through the production checkers in separate
children. Process groups are killed after completion or timeout; dependencies,
models, credentials and remote destinations are never acquired by this command.

Documentation checks execute all four public categories. Missing Mermaid tooling
blocks the gate. Methods checks audit every canonical exemplar in rendered mode.
The macOS checks require a real Darwin host: process acceptance observes OS exit
transport and a real timeout; rendering acceptance invokes Pandoc and checks the
actual HTML content. Full native-format acceptance remains a separate gate.

An exemplar `:pipeline` selection executes the current complete core plan with
cleanup and shared infrastructure explicitly omitted. It retains the actual plan,
ordered outcomes, run ID, and plan digest; partial or cached outcomes cannot pass.

Additional domain/live integrations can declare a source-owned callable under
`[tool.template.acceptance_producers]`, keyed by `domain` or `live:<capability>`.
Its `module:callable` must originate in that public project's `src/` and accept
`project_root` and `timeout_seconds`. It must return actual kind-specific facts,
including its own independently executed failing controls. Returning a summary
status or a fixture receipt cannot grant acceptance.

Built-in adapters execute the actual EDA fresh-kernel producer, Formal's pinned
Lean/TLC producer with acquisition disabled, and the three literature exemplars'
existing unpaid producer APIs. Literature execution additionally requires
`--local-model` naming an already-installed loopback Ollama model. Their complete
native receipts remain independently bound alongside process observations;
missing tool, model or required provider inputs leave explicit blockers.

`root:sandbox:transfer` records a blocker until the exact provider, authorized
sandbox destination and existing authorization are selected. A local copy or
dry run cannot establish independent remote retrieval. Production publication
is outside this executor.

`--all` selects all declared auxiliary kinds; `--installed` reuses the actual
installed/export executor, with repeatable `--installed-interpreter 3.14=/path`
arguments. Both write `receipt.json` under the nominated fresh evidence directory.
Specialized adapters retain the existing SIA numeric/Docker, autoscientists matched
comparison, autopoiesis selected-child numerical results, Active Inference pymdp
and Lean, Formal network faults, public resource execution, publication PDF/PPTX
and raster, descriptor checksum/row verification, and methods DSL compiler facts.
They use actual public source APIs. Model and Docker execution requires explicit
existing `--local-model` and `--docker-image-id` selection. Unimplemented or
unavailable declared obligations remain blocked; these adapters do not establish
complete readiness until every required source obligation passes.

Process v2 evidence retains original producer-root/interpreter observations.
Readers reconstruct the original argv using confined relative spec/fact paths;
they do not open historical producer paths or executable bytes. The fresh owned
bytecode cache is removed after process-group cleanup. Its observed original path
remains in runtime facts. Hash equality establishes byte consistency; source
origin relies on the exact-commit reviewed producer and hosted handoff context.

The approved GitHub Actions transfer uses the existing repository/run and token:

```bash
python -m infrastructure.project.public_acceptance_auxiliary_cli \
  --prepare-transfer --export-receipt output/readiness/installed/receipt.json
```

Upload only the returned `upload_path` as `root-candidate-export`, with one-day
retention and missing-file errors enabled. Retain the official action's complete
outputs JSON under `output/readiness`, then use the official download action with
that exact artifact ID into a fresh directory. Finally:

```bash
python -m infrastructure.project.public_acceptance_auxiliary_cli \
  --emit-transfer --export-receipt output/readiness/installed/receipt.json \
  --upload-outputs output/readiness/upload-outputs.json \
  --downloaded-directory output/readiness/sandbox-download \
  --repository "$GITHUB_REPOSITORY" --github-run-id "$GITHUB_RUN_ID" \
  --source-commit "$GITHUB_SHA" --evidence-dir output/readiness/sandbox-transfer
```

The producer independently admits the original Root ZIP, observes actual checkout
HEAD and scoped GitHub artifact/repository API responses, requires exact original
upload ID/digest/repository/run/commit, and reads retrieved ZIP bytes. The transfer
validator additionally requires the reader's independently admitted Root export.
No local simulation or asserted remote-success flag can satisfy this contract.

After the installed matrix completes, prepare its current non-root runtime
providers with `--prepare-runtime-providers --installed-receipt <receipt>`. The
JSON `provider_wheel_arguments` array supplies exact `--provider-wheel` argv pairs
for the complete public runtime matrix. Discovery uses declared local dependency
closures, full installed-gate admission, current-source wheel inspection, and
original byte hashes; it never guesses wheel filenames or substitutes an SDK.

The deterministic domain adapters consume the actual source-owned numerical,
registration, tree, prose, token-plan, corpus and repository-metrics producers.
They retain full measurements and exact consumed-input hashes inside the
supervised raw facts. Independent admission reconstructs analytic textbook
curves and quadratic objectives/gradients; recomputes MNIST confusion matrices
and accuracy from source labels; and rechecks source registration, DAG,
configured prose, seeded token, search, bibliometric and phase contracts.
The four-candidate MNIST budget retains the fifth candidate as deferred, with
no invented measurements. Literature fixture replay and fixture bibliometrics
are explicitly fixture evidence; their domain success does not certify model
execution or live retrieval. Every adapter additionally executes the actual
production checker on a corrupt input in a separately supervised child.

Pipeline receipts use `template-auxiliary-pipeline-portable-v1`. The genuine core
executor runs all source-required stages in a disposable complete public source
copy outside the candidate Git worktree, using the explicitly nominated existing
prepared interpreter. No executable or virtual environment is copied. Exact
tracked public output fixtures are retained as bound inputs when authored tests
require them; every stage must still freshly succeed. The benchmark plugin's
storage moves into the owned output control directory through its supported
option. Every fresh output byte and the original execution record are retained.

Admission reads the original process/spec/streams and complete before/after
source records, Python/distribution/tool components, aggregate environment
hashes and hashed key census. Only controlled public environment values are
recorded; credential values are never read or forwarded. A separate fresh,
credential-free reader process recompiles the complete current logical source
plan and reconstructs its original identities from admitted custody. It never
opens historical producer paths or executables. General pipeline and cache
identities are unchanged. Per-key hashes cannot reconstruct the original
aggregate environment hash: integrity checks retain both original hashes and
all component comparisons, while authenticated same-repository exact-SHA hosted
handoff establishes origin. An unsigned local bundle alone cannot establish that
origin if all retained bytes and hashes are rewritten consistently.

The QR runtime v2 retains original linked libzbar path, SHA256, byte count and
regular-file metadata before and after actual decoding. It preserves genuine
loader, version and decode process records without redistributing installed
library bytes. Portable replay checks exact record fields, integer outcomes
(0 or 4), exact False supervision flags, empty diagnostics, original executable
observations and linked-core observations. Hash integrity does not authenticate
producer origin; the enclosing source/parser/SDK custody provides that context.
Replay never reopens the original scanner/core prefix. Genuine baseline,
wrong-payload and unreadable QR controls exercise actual native children and
reject rehashed malformed outcomes, supervision flags and custody metadata.
