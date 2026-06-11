"""Performance benchmarks for infrastructure modules.

Tests in this package are marked with ``@pytest.mark.bench`` and are
part of the full infra suite. Run a benchmark-only pass with ``-m bench`` when
you want the timing signal without the rest of the tests.

To run them explicitly::

    uv run pytest tests/infra_tests/benchmark/ -m bench --benchmark-only \
        --benchmark-min-rounds=3 --timeout=180

All benches follow the no-mocks policy: real ``tmp_path`` filesystems,
real subprocesses, real ``pytest-benchmark`` fixtures.
"""
