# TODO — template_pools_rules_tools

Forward-only backlog for the pools/rules/tools integration exemplar.

## Current validation evidence

- [x] Project skeleton created
- [x] `src/` modules implemented with graceful fallbacks
- [x] `tests/` cover fonds, rules, tools, and integration
- [x] `scripts/` are thin orchestrators
- [x] `manuscript/` sections drafted

## Integrity and template-status gaps

- [ ] Verify test coverage ≥ 90% on `src/` (`uv run pytest --cov=src --cov-fail-under=90`)
- [ ] Confirm all `pytest.mark.skipif` guards have accurate file-path checks

## Configurable-surface gaps

- [ ] Extend `integration:` block in `manuscript/config.yaml` when new public fonds/rules/tools ship

## Documentation and signposting gaps

- [ ] Add `.agents/skills/template-pools-rules-tools/SKILL.md` Hermes skill

## Test and validator gaps

- [ ] Add strong-rule semantic evaluation beyond structural parsing

## Ordered improvement ladder

1. Add a fourth fond type (e.g. `template_models`) once the fond exemplar exists
2. Extend `rules_applier.py` to evaluate strong rules programmatically
3. Add `scripts/04_validate_strong_rules.py` gate
