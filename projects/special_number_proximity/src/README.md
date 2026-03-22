# src/

| Module | Responsibility |
|--------|----------------|
| `continued_fractions.py` | Float CF terms, exact rational CF, convergent iterator |
| `rational_distance.py` | $\delta_Q$ and $\mu_Q$ ($q^2|x-p/q|$); fractional / mod-1 |
| `cf_distance.py` | Best distance among convergents up to $q \leq Q$ |
| `diophantine_bounds.py` | $\|qx\|/q$ form of $\delta_Q$, Dirichlet residual tools |
| `constants.py` | `NamedConstant` registry |
| `sampling.py` | Uniform, Beta, quadratic-mod-$1$ draws |
| `statistics_compare.py` | Batch helpers, percentiles, comparison tables |

Imports assume `src/` on `PYTHONPATH` (see `tests/conftest.py` and project `pyproject.toml`).
