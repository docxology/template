# Testing Philosophy — Active Inference

- **Cross-track consistency.** Tests verify that analytical results match
  simulation boundaries and manuscript claims agree across tracks.
- **No mocks.** Real computation, real pymdp runs, real filesystem.
- **Deterministic seeds.** All random processes use explicit seeds.
- **Optional path gating.** Live services (Ollama, Lean) are opt-in
  behind `# pragma: no cover` markers.
- **Coverage floor:** 90% on `src/`.
