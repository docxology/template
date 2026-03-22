# tests/ — `special_number_proximity`

| File | Coverage focus |
|------|----------------|
| `test_continued_fractions.py` | Exact rationals, $\varphi$ partial quotients, empty convergents |
| `test_rational_distance.py` | Exact hits, $\mu_Q$, validation errors, fractional/mod-1 |
| `test_rational_distance_exhaustive.py` | Brute vs scan for $x\in[0,1)$, $Q\le 30$ |
| `test_batch_implementation_parity.py` | Vectorised vs scalar batch paths |
| `test_cf_distance.py` | Convergent lower envelope vs $\delta_Q$ |
| `test_diophantine_bounds.py` | Lattice identity, Dirichlet residual |
| `test_constants.py` | Registry keys and classes |
| `test_sampling.py` | Uniform, Beta, quadratic draws |
| `test_statistics_compare.py` | Batching, ranks, tables |
| `test_statistics_compare_extended.py` | Midrank, distribution summaries, `reference_percentiles` |
| `test_summarize_q_squared.py` | Optional $\mu_Q$ columns |
| `test_init_exports.py` | `src/__init__.py` re-exports |
| `test_proximity_monte_carlo_module.py` | `run_proximity_study` smoke |
| `test_lattice_crosscheck_script.py` | Lattice script import/run |

No mocks: numerical checks only.
