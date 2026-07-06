# template_autopoiesis — TODO

## Current Validation Evidence
- **Tests**: 410 tests, 90.33% coverage
- **Ruff**: clean
- **Mypy**: clean (48 source files)
- **Pre-render gate**: clean
- **Tracked projects guard**: clean
- **Public scope**: registered as `templates/template_autopoiesis`

## Integrity and template-status gaps
- [x] All canonical exemplar files present (README, AGENTS, pyproject, .gitignore, TODO, manuscript/*)
- [ ] Cover art: simplified (no QR seal with grammar_hash, no gradient glow, no seed dots)
- [ ] `src/emit_templates.py`: rebuild the full @@KEY@@-templated file bodies for generated children

## Configurable-surface gaps
- [x] `manuscript/config.yaml` — full grammar with 6 slots
- [x] `manuscript/config.yaml.example` — fork-safe copy
- [x] `.agents/skills/template-autopoiesis/SKILL.md` — Hermes-compatible skill
- [x] `publish/zenodo_metadata.json` — deposit metadata
- [ ] `manuscript/references.bib` — placeholder only, needs real DOI entry

## Documentation and signposting gaps
- [x] README — use-this-template, config-entry-points, template-integrity signposts all present
- [x] AGENTS.md — full architecture, module inventory
- [x] CHANGELOG.md — Wave 9 filled
- [x] STANDALONE.md — standalone usage guide
- [x] SYNTAX.md — grammar syntax reference
- [x] SPEC.md — full spec document, Phase 10 partially checked
- [x] IMPROVEMENTS.md — all items A-E resolved

## Test and validator gaps
- [x] 410 tests across 24 test files
- [ ] `sealing.py` at 51% coverage — qrcode/pyzbar import paths
- [ ] `verify.py` at 88% coverage — seal verification paths
- [ ] `cli.py` at 75% coverage — subprocess-based commands
- [ ] Manuscript figure labels need alignment with actual generated output

## Ordered improvement ladder
1. Restore full cover art with QR seal, gradient glow, seed dots
2. Rebuild `src/emit_templates.py` for child project generation
3. Complete `references.bib` with real DOIs
4. Align manuscript figure labels with actual generated filenames
5. Wire into CI coverage gate
6. Cover sealing.py, verify.py, cli.py coverage gaps