from invariants import all_invariants_pass, run_invariants


def test_core_invariants_pass() -> None:
    results = run_invariants()
    assert results
    assert all_invariants_pass(results), results
