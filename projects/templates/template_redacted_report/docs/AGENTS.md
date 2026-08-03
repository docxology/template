# docs - AGENTS.md

Design-decision and process reference for the `template_redacted_report`
exemplar.

| Document | Role |
| --- | --- |
| `README.md` | Quick orientation: design decisions, verification workflow, boundary rules. |
| [`../AGENTS.md`](../AGENTS.md) | Root exemplar contract: ground truth, commands, boundaries. |
| [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) | Manuscript editing rules (prose focus, figure protocol). |

## When to update

- A surprising local design choice (e.g. a text-free projection decision, the
  mssim-to-swtpm proxy, the Kmyth FlushContext patch, figure determinism
  constraints) is introduced or changed → record it in `README.md`.
- Keep this folder aligned with the root `AGENTS.md` and the manuscript.
