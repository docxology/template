# Agent Notes

`projects/templates/template_active_inference/docs/reference/` is documentation
only — reference lookups, not business logic. Keep logic in `../../src/`,
orchestration in `../../scripts/`, and generated artifacts under `../../output/`.

- **method-inventory.md** must stay in step with the methods actually defined in
  `../../src/`; when you add or rename a method/track, update its row here.
- **rendering-reproducibility.md** documents the deterministic render contract
  (fixed seeds, pinned inputs); update it when the render pipeline changes.

Every directory under `docs/` carries a `README.md` (user-facing) and an
`AGENTS.md` (this technical note) — the repo's doc-pair lint enforces both.
