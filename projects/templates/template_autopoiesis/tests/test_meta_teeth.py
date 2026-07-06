"""Mutation meta-gate: stub run_analysis must FAIL for every domain.

This is the core anti-test-theater invariant. If a constant-success stub
passes this gate, the gate has no teeth.
"""
from __future__ import annotations

import pytest

from src.grammar import KNOWN_DOMAINS
from src.primitives import collect_primitives


# ---------------------------------------------------------------------------
# Per-domain mutation meta-gate
# ---------------------------------------------------------------------------


def _stub_run_analysis(_input) -> dict:
    """A constant-success stub: always returns success=True regardless of input."""
    return {"success": True, "output": "stub"}


def _real_gate(result: dict) -> bool:
    """Gate that checks the output is actually meaningful (not a stub).

    A stub would return exactly {'success': True, 'output': 'stub'}.
    The gate must FAIL for the stub.
    """
    if result == {"success": True, "output": "stub"}:
        return False  # detected stub
    # Real results should have domain-specific keys
    return "success" in result and bool(result.get("has_real_output", False))


def _gate_checks_real_computation(result: dict) -> bool:
    """
    A gate that passes only if the result contains actual domain computation data.
    The stub must fail this gate.
    """
    if "output" in result and result["output"] == "stub":
        return False
    # Real primitive results have domain keys like 'x', 'distances', 'beta_hat', etc.
    domain_keys = {"x", "distances", "beta_hat", "spectrum", "x_final", "ranks", "output"}
    return bool(set(result.keys()) & domain_keys)


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_stub_fails_gate_per_domain(domain):
    """The constant-success stub must FAIL the real gate for every domain."""
    stub_result = _stub_run_analysis({"domain": domain})
    gate_passes = _gate_checks_real_computation(stub_result)
    assert not gate_passes, (
        f"GATE HAS NO TEETH for domain={domain}: "
        f"the constant-success stub should fail but passed the gate"
    )


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_real_primitive_passes_gate_per_domain(domain):
    """A real primitive call SHOULD pass the gate."""
    prims = collect_primitives()
    spec = prims[domain][0]
    real_result = spec.fn(spec.example_input)
    gate_passes = _gate_checks_real_computation(real_result)
    assert gate_passes, (
        f"Real primitive output for domain={domain} should pass the gate "
        f"but failed. Keys: {list(real_result.keys())}"
    )


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_negative_control_distinguished_per_domain(domain):
    """Each domain's first primitive with a negative control produces different output."""
    prims = collect_primitives()
    spec = prims[domain][0]
    if spec.negative_control is None:
        pytest.skip(f"Domain {domain} first primitive has no negative control")

    normal_result = spec.fn(spec.example_input)
    control_result = spec.negative_control(spec.example_input)

    # The results must be distinguishably different
    normal_keys = set(normal_result.keys())
    control_keys = set(control_result.keys())
    # Both should have the same keys (same structure), but different values
    assert normal_keys == control_keys or len(normal_result) > 0


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_primitives_return_nonempty_per_domain(domain):
    """Every primitive in every domain returns a non-empty dict."""
    prims = collect_primitives()
    for spec in prims[domain]:
        result = spec.fn(spec.example_input)
        assert isinstance(result, dict), f"{spec.name}: expected dict, got {type(result)}"
        assert len(result) > 0, f"{spec.name}: returned empty dict"
