# Data

`mnist_small.npz` is a deterministic, balanced subset of the MNIST handwritten
digit database. It contains 200 training images and 50 test images per class,
stored with the original 28 by 28 grayscale pixels.

The default AutoResearch run reads this local file only. It does not download
MNIST during tests, analysis, rendering, validation, or CI. Source-file hashes,
subset seed, class counts, and the subset archive hash are recorded in
`mnist_small_provenance.json`.

## Fixture Maintenance

Regeneration is an explicit manual maintenance action:

```bash
uv run python projects/templates/template_autoresearch_project/scripts/regenerate_mnist_fixture.py
```

The script downloads upstream MNIST archives, verifies their fixed HTTPS source,
size, and SHA-256 hashes, then rewrites `mnist_small.npz` and
`mnist_small_provenance.json`. It is not imported by the default pipeline and is
not called by tests, analysis, rendering, validation, or manuscript hydration.
