"""Performance benchmarks for infrastructure modules.

Tests in this package are marked with ``@pytest.mark.bench`` and are
**skipped by default** (see root ``pyproject.toml#[tool.pytest.ini_options].addopts``,
which appends ``-m 'not slow and not bench'``).

To run them explicitly::

    uv run pytest tests/infra_tests/bench/ -m bench --benchmark-only \
        --benchmark-min-rounds=3 --timeout=180

All benches follow the no-mocks policy: real ``tmp_path`` filesystems,
real subprocesses, real ``pytest-benchmark`` fixtures.
"""
