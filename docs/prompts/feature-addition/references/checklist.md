# Feature addition checklist

- [ ] Business logic only in `src/` or `infrastructure/`
- [ ] Script is thin orchestrator
- [ ] Tests: no mocks; coverage floor met
- [ ] Type hints + docstrings on new public APIs
- [ ] Logging via `get_logger`
- [ ] Deterministic outputs (seeds, MPLBACKEND=Agg)
- [ ] Manuscript refs use injectors, not hand-typed numbers
- [ ] AGENTS.md / README updated
- [ ] No cross-project imports
- [ ] Root venv includes deps if project has no local `.venv`
