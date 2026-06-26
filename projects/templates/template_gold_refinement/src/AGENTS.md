# src/ — Gold Refinement Domain Logic

## Overview

The `src/` directory contains the importable domain logic for the gold-refinement
exemplar. The refinery pipeline (`refinery.py`, `purity.py`) models the five
metallurgical stages; the mega-madlib engine (`config.py`, `composition.py`)
handles deterministic token injection; `assay.py` validates claims against
evidence; and `manuscript_variables.py` generates all `{{TOKEN}}` values.

## Layer Contract

`src/` must not import `infrastructure.*`. All infrastructure coupling belongs
in `scripts/` (thin orchestrators).

## Modules

| Module | Role |
|--------|------|
| `refinery.py` | Five-stage pipeline (ore → smelting → assaying → cupellation → certification) with monotone purity enforcement |
| `purity.py` | Karat grading (9K–24K), nine-nines certification, purity formatting |
| `config.py` | Mega-madlib config schema: lexicon, slots, section conditions, narrative moves |
| `composition.py` | Deterministic token selection via seeded SHA-256 digest |
| `assay.py` | Claim-evidence validation (the assaying stage) |
| `manuscript_variables.py` | Generates all `{{TOKEN}}` values for manuscript injection |

## Key Design Rules

- Purity must increase monotonically across stages (`assert_monotone_increase`)
- Token selection is deterministic: same seed + lexicon = same plan
- Every `{{TOKEN}}` in manuscript source must be produced by `generate_variables()`
- Config owns all prose choices (lexicon, slots, narrative moves)
