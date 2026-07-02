# Testing Philosophy — Template Madlib

- **Real configs.** All tests load real YAML config files.
- **Deterministic outputs.** Fixed seeds ensure reproducible token selections.
- **Contract tests.** Every config field has a validity test.
- **No mocks.** Real data, real subprocesses.
- **Coverage floor:** 90% on `src/`.
