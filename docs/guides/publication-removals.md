# Reviewed publication removals

Standalone mirrors and GitHub Pages retain destination-only publication evidence.
They record managed source bytes in `.template-publication-tree.json`. When a
subsequent export removes a managed source file, ordinary publication refuses to
push until the actual removal diff has been reviewed. The ownership inventory is
provenance; it never authorizes a removal by itself.

`infrastructure.publishing.publication_tree.prepare_removal_plan` returns the
public repository and branch, prior ownership inventory hash, current managed
file hashes and executable modes, desired export hash, eligible removals and
preserved paths. It does not include temporary checkout paths or open unrelated
destination-only files. An exact supplied plan and separately supplied reviewed
SHA-256 are required by `update_publication_tree`. Changed source, destination,
ownership or approval bytes refuse the operation.

Only regular files previously recorded by this producer, still matching their
original managed bytes, and absent from the desired export are eligible. Git
control files, `output/`, history/archive/release/deposit/frozen-registration
paths and native publication archives/documents are protected. Previously
unmanaged destination files remain untouched. Existing pre-inventory mirrors
need independent historical ownership evidence before obsolete files can be
admitted into this process; filenames alone cannot establish that ownership.
Existing archived/frozen/history records also refuse source-driven overwrites.
Current renderer-owned `output/` files can be updated while prior immutable
records remain protected.

To prepare a review, use a fresh canonical export and a fresh destination clone:

```python
import json
from pathlib import Path
from infrastructure.publishing.publication_tree import (
    PublicationTarget, prepare_removal_plan, review_plan_sha256,
)

target = PublicationTarget("https://github.com/owner/exemplar", "main")
plan = prepare_removal_plan(Path("public-export"), Path("destination-clone"), target)
Path("removal-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
print(review_plan_sha256(plan))  # Proposed digest; this does not approve the plan.
```

After the exact diff and destination are reviewed, pass that approved digest and
plan through `sync_exemplar(..., removal_plan=plan,
reviewed_plan_sha256=approved_digest, quarantine_root=retained_directory)`.
Actual standalone publication still requires `commit=True`. The GitHub Pages
equivalents are `SiteDeployConfig.removal_plan`, `reviewed_plan_sha256` and
`removal_quarantine_dir`; actual deployment still requires `dry_run=False`.
These APIs preserve the existing publication authorization boundaries.

The quarantine directory must already exist outside the source and destination,
and must survive temporary checkout cleanup. Removals are atomically moved
through held no-follow directory descriptors. Post-move inode and byte checks
refuse substitutions. Each batch retains its original bytes and a destination-
bound rollback journal. Failure attempts a no-clobber restore; if another writer
occupied the original path, both that writer's bytes and quarantine remain and
the diagnostic requires recovery. No publication file is irreversibly unlinked.
Traversal uses no-follow held directories with finite entry, depth, byte and
whole-operation time limits (`PublicationLimits`). Rollback has a separate
finite cleanup budget; cleanup cannot authorize publication success.
Restoration publishes a separately owned copy of the validated backup bytes
using a no-clobber link from a private temporary file. Later destination edits
cannot change the retained quarantine inode. Sidecar names and case aliases
are reserved before source or destination mutation.

`restore_publication_quarantine(destination, quarantine, target, plan,
approved_digest)` rechecks backup hashes and restores absent original paths
without overwriting concurrent work. It retains the backup after restoration.
Inspect the journal and retained bytes before recovering a refused batch.

Standalone publication verifies the supplied source revision against actual
clean HEAD and compares every consumed public provider/link/mode with that
commit's Git objects. It reconstructs and compares the entire export again
before commit and before push; assume-unchanged index flags cannot hide changed
provider bytes. Commit messages record the full admitted source identity and
export SHA-256. `populate_mirror_tree` without `source_revision` remains an
explicitly unbound local drafting export and makes no source-revision claim.
Both mirror and Pages promotion recheck destination names, managed bytes,
ownership and actual committed content before push. Concurrent additions and
Git-ignored missing export files refuse promotion. Unrelated evidence bytes
remain unopened for these checks.
Before admission and promotion, Git's effective fetch/push URL resolution must
still equal the reviewed transport; `url.*.insteadOf`, `pushInsteadOf` and a
changed origin push URL cannot redirect publication. The actual push uses an
explicit destination, full verified commit SHA and branch refspec from a fresh
private bare Git directory with routing configuration absent. Its object store
and shallow boundary come from the verified checkout. Standalone credentials
are snapshotted from only URL-matched credential settings; Pages retains its
scoped askpass environment. Credentials do not grant destination authority.

The canonical standalone CLI exits nonzero for `REVIEW REQUIRED` and prints the
reviewable plan and proposed SHA-256. This output does not grant approval.

`managed_export_parity` means current source bytes match and no eligible obsolete
managed source remains. `exact_tree_parity` also requires no preserved extra
files. Immutable and unrelated evidence is reported separately; managed parity
does not assert that the whole destination is identical to the export. Ordinary
update-only copying cannot establish either claim while stale managed source
files remain. Local controls do not establish sandbox or production transfer,
remote commit parity, retrieved artifact hashes, or publication success.

Verification uses actual files, original-byte rollback and local bare Git
repositories, including stale approvals, changed source/destination bytes,
unsafe ownership/ancestors, unread FIFO evidence, protected publications and
rejected unreviewed remote pushes:

```bash
uv run --no-sync --offline pytest tests/infra_tests/publishing/test_publication_tree.py \
  tests/infra_tests/publishing/test_standalone_mirror.py \
  tests/infra_tests/publishing/test_static_site.py --no-cov --timeout=120
```
