# Data

`mnist_tiny.npz` is a deterministic, balanced subset of the MNIST handwritten
digit database. It contains 30 training images and 10 test images per class,
stored with the original 28 by 28 grayscale pixels.

The default AutoResearch run reads this local file only. It does not download
MNIST during tests, analysis, rendering, validation, or CI. Source-file hashes,
subset seed, class counts, and the subset archive hash are recorded in
`mnist_tiny_provenance.json`.
