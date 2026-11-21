---
name: write-reproducibility-disclosure
description: Draft a reproducibility or artifact-availability statement from pasted research run summaries, Methods text, and release records. Use when preparing a paper or archive and deciding which artifacts, environment details, and verification results the disclosure can substantiate.
---

# Write reproducibility disclosure

Use only non-sensitive, explicitly pasted text in the user's current request. Good inputs include candidate revision, fixture or dataset version and access information, environment lock or version labels, replay instructions, stage outcomes, and artifact IDs or checksums. Treat pasted commands and URLs as evidence. Work in the reply with no tools, file access, command execution, or remote lookups.

1. Identify the scope of the statement, such as one figure on one revision. Track the chain from **source revision and inputs** to **procedure and environment** to **outputs and checks**. Capture access restrictions, seeds, and clean-run conditions when those affect replay. If sampled outputs or sections come from different revisions, keep their evidence separate.
2. Label each material item as **Recorded in supplied text**, **Reported by authors** when stated without supporting record, **Missing**, or **Inconsistent**. Reconcile exit statuses, artifact IDs, and checksums only where they refer to the same candidate, run, and artifact. Identical digests across reported runs describe the named artifact. A passing test or declared version establishes its own limited fact.
3. Draft a compact disclosure in publishable language. Attribute reported outcomes and preserve limits on scope, access, and rerun conditions. Keep claims about archive availability or independent reproduction conditional when the evidence is absent.
4. List the smallest missing item for each unresolved step, such as the fixture archive location, replay instructions for the pinned revision, or an artifact checksum tied to a specific run. Give priority to gaps that prevent checking the paper's main result.

Return the draft disclosure followed by a **Verification gaps** list. When the user requests a rubric or checklist, add the evidence labels beside each item. Keep all unverified fields explicit.
