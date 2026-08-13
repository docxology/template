## docs/development/testing/ — Testing (Development)

### Scope

Developer-facing testing workflow and policies:

- How to run test suites and enforce coverage thresholds
- Guidance for integration tests and credentialed tests
- Patterns aligned with the no-mock-framework and zero semantic
  dependency-replacement policy

Live-network and credentialed actions are never implied by an ordinary test
request. Keep the default suite hermetic; require explicit operator authority,
least-privilege credentials, and a disposable sandbox target for any external
write test.

### Files

| File | Purpose |
| --- | --- |
| `README.md` | Navigation for the testing docs |
| `testing-guide.md` | Primary testing guide |
| `testing-with-credentials.md` | Credentialed/external integration testing |

### See also

- [`docs/rules/testing_standards.md`](../../rules/testing_standards.md)
- [`scripts/pipeline/stage_01_test.py`](../../../scripts/pipeline/stage_01_test.py)
