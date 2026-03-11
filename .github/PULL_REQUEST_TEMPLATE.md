# Pull Request

## Description

<!-- Brief summary of what this PR does and why. -->

Closes #<!-- issue number(s) -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Security enhancement
- [ ] Refactor / cleanup
- [ ] CI/CD update

## Pipeline Stage Affected

<!-- Which pipeline script(s) / stage(s) are touched? -->
- [ ] `00_setup_environment` — environment setup
- [ ] `01_run_tests` — test execution
- [ ] `02_run_analysis` — project analysis
- [ ] `03_render_pdf` — PDF rendering
- [ ] `04_validate_output` — output validation
- [ ] `05_copy_outputs` — copy final deliverables
- [ ] `06_llm_review` — LLM review (optional)
- [ ] `infrastructure/` — core library
- [ ] `.github/` — CI/CD only
- [ ] None / documentation only

## Testing

- [ ] All existing tests pass (`uv run pytest tests/ projects/*/tests/ -m "not requires_ollama"`)
- [ ] New tests added for any new functionality
- [ ] Coverage requirements met (infra ≥ 60%, projects ≥ 90%)
- [ ] Tested locally with `./run.sh --pipeline` or relevant stage

## No-Mocks Confirmation

- [ ] This PR contains **no** use of `MagicMock`, `mocker.patch`, `unittest.mock`, or any mocking framework in tests

## Checklist

- [ ] Code follows the Thin Orchestrator pattern (business logic in `src/`, not scripts)
- [ ] AGENTS.md / README.md updated where relevant
- [ ] Breaking changes documented in PR description or linked issue
- [ ] Security considerations addressed (no hard-coded credentials, no new untrusted inputs)
- [ ] Added to `CHANGELOG.md` or commit message is self-documenting
