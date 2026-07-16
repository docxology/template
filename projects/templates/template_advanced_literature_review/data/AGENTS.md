# Data authoring contract

- Keep only small, reviewable, domain-input fixtures here.
- Treat `manuscript/config.yaml` as the source of truth for active search
  phases; defaults in this directory must not silently override it.
- Keep generated or downloaded records under `output/`, never `data/`.
- Document every added fixture in `README.md` and cover its consumer with a
  real parser or integration test.
