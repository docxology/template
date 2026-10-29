# Versioned release notes

These source-controlled notes summarize each intended platform release. Its
GitHub Release and authenticated workflow artifacts establish publication;
a note file or image alone does not establish completed acceptance.

- [4.3.0 release intent](v4.3.0.md): two-step coordinated minor metadata preparation (4.2.0 applied but unpublished), shared CI composite actions, duration-weighted shard balancing, a modular sharded/parallel publication-output gate whose per-project receipts `release.yml` retains (blocking versus `review_required` severities), a root-plus-exemplar release version identity gate, a two-minor installed matrix that nominates a lock's exact sdist for target minors without wheels (torch/triton/cuda-bindings and hypothesis refreshed for cp315), forkable exemplar copies and retained custody contracts. Acceptance and publication remain pending.
- [4.1.0 release intent](v4.1.0.md): explicit minor preparation, source/runtime custody repairs, bounded native model requests and lossless publication assets. Acceptance and publication remain pending.
- [4.0.2 historical candidate](v4.0.2.md): bounded CI feedback, cold diagnostic preflight, native revalidation and coordinated version preparation.
- [4.0.1 preparation](v4.0.1.md): exact platform bindings, source/native custody and tag-selected publication artifacts; superseded before publication.
- [4.0.0 preparation](v4.0.0.md): immutable execution, complete SDK packaging and source-bound acceptance.

See [AGENTS.md](AGENTS.md) for evidence and image custody.
