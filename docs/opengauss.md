# Open Gauss (fep_lean)

In this repository, **Open Gauss** refers to the **[math-inc/OpenGauss](https://github.com/math-inc/OpenGauss)** Lean assistant CLI (`gauss`), integrated under [`projects/fep_lean/`](../projects/fep_lean/).

It does **not** refer to Huawei OpenGauss DBMS.

The `fep_lean` Python code **does** persist formalization sessions in **SQLite** via `OpenGaussClient` in [`projects/fep_lean/src/gauss/client.py`](../projects/fep_lean/src/gauss/client.py) (default `{GAUSS_HOME}/codomyrmex_state.db`). That client is unrelated to the Huawei product.

Full detail: [projects/fep_lean/docs/opengauss.md](../projects/fep_lean/docs/opengauss.md).
