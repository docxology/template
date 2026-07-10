# data/fixtures - template_data_descriptor

Real, public, synthetic data files described by `data/example_descriptor.json`.

- `measurements.csv` — one synthetic sample per row (12 rows): `sample_id`,
  `subject_id`, `group`, `value`, `collected_on`, `instrument`.
- `subjects.csv` — one synthetic subject per row (6 rows): `subject_id`, `site`,
  `enrolled_on`.

These files are deterministic and safe to commit. Their sha256 checksums and row
counts are declared in the descriptor and verified against these bytes by
`verify_descriptor_files()` in `src/data_descriptor/verification.py`. Editing a
file here without updating the descriptor will flip its verification status to a
mismatch and fail the test suite — that is the intended contract.

Real restricted datasets must stay outside the public repository and be
represented by descriptor metadata and checksums only.
