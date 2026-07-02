# Testing Philosophy — AutoScientists

- **No mocks (absolute).** Real deterministic objects only — no
  `MagicMock`, `mocker.patch`, or `unittest.mock`.
- **Deterministic.** All tests use fixed seeds and real computation.
- **Ablation tests.** Every mechanism toggle is tested in isolation.
- **Negative controls.** Gates must fail on stale or malformed evidence.
- **Coverage floor:** 90% on `src/`.
