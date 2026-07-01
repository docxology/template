"""Regression pins for the controlled-method specification DSL exemplar.

Manuscript: projects/templates/template_methods_paper/manuscript/03_results.md.

This exemplar's contribution is a small, tested DSL for specifying controlled
methods: units/dimensional-safety, a controlled vocabulary, four staged
validation gates, and a deterministic Kahn's-algorithm compiler with SHA-256
plan hashing. These pins bind the manuscript's quantitative claims to the
source: each value is re-derived by calling ``src.methods_dsl.compile_method``,
``run_all_gates``, and ``demo_chain_report`` on the two shipped worked example
methods (``PBSPreparation`` / ``SensorCalibrationSweep``) -- never by
hand-copying a number from the manuscript.

The two full SHA-256 plan hashes are the strongest pins: ``compile_method``
uses a canonical sorted-key JSON encoding plus a deterministic topological
sort, so the digest is byte-exact and reproducible across processes and
platforms. The manuscript displays only the first 12 hex characters
(``{{PBS_PLAN_HASH}}`` / ``{{CALIBRATION_PLAN_HASH}}``); these tests bind the
full digest, so any change to a step, its order/kind/target, or the method
target/version flips the hash and fails the test.

No mocks: real deterministic objects only, in line with the repo no-mock policy.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_methods_paper"

_PKG_ALIAS = "_methods_paper_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    Registering under a namespaced key keeps the real tested functions in
    scope (no mocks) and stays collision-free regardless of collection order.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = PROJECT_ROOT / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(PROJECT_ROOT / "src")],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _import_submodule(dotted: str) -> ModuleType:
    _load_src_package()
    return importlib.import_module(f"{_PKG_ALIAS}.{dotted}")


_dsl = _import_submodule("methods_dsl")
compile_method = _dsl.compile_method
run_all_gates = _dsl.run_all_gates
demo_chain_report = _dsl.demo_chain_report
pbs_preparation_method = _dsl.pbs_preparation_method
sensor_calibration_method = _dsl.sensor_calibration_method
all_example_methods = _dsl.all_example_methods


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int | str) -> None:
    expected = entry["value"]
    if isinstance(expected, str):
        # Byte-exact match for SHA-256 hex digests (tolerance is meaningless here).
        assert observed == expected
    else:
        tolerance = entry.get("abs_tolerance", 0)
        assert observed == pytest.approx(expected, abs=tolerance)


@pytest.fixture(scope="module")
def compiled_plans() -> dict[str, Any]:
    """Re-derive both compiled plans exactly as the analysis script does."""

    pbs_plan = compile_method(pbs_preparation_method())
    calibration_plan = compile_method(sensor_calibration_method())
    return {"PBSPreparation": pbs_plan, "SensorCalibrationSweep": calibration_plan}


def test_compiled_plan_hash_claims_rederive_from_source(
    load_pinned_values: Any,
    compiled_plans: dict[str, Any],
) -> None:
    """Bind both full SHA-256 plan hashes + step counts to a fresh source compile.

    03_results.md / Compiled-plan summary table. The manuscript shows the
    first 12 hex of each hash ({{PBS_PLAN_HASH}} / {{CALIBRATION_PLAN_HASH}});
    these pins bind the full digest, which is byte-exact and deterministic.
    """

    pinned = load_pinned_values("template_methods_paper")
    pbs_plan = compiled_plans["PBSPreparation"]
    calibration_plan = compiled_plans["SensorCalibrationSweep"]

    _assert_pin_matches(_pin(pinned, "pbs_plan_hash"), pbs_plan.plan_hash)
    _assert_pin_matches(_pin(pinned, "calibration_plan_hash"), calibration_plan.plan_hash)

    _assert_pin_matches(_pin(pinned, "pbs_step_count"), len(pbs_plan.steps))
    _assert_pin_matches(_pin(pinned, "calibration_step_count"), len(calibration_plan.steps))

    # Sanity: the manuscript's rendered 12-hex prefix must be the head of the
    # pinned full digest (guards against a truncated-vs-full mismatch).
    assert pbs_plan.plan_hash[:12] == _pin(pinned, "pbs_plan_hash")["value"][:12]
    assert calibration_plan.plan_hash[:12] == _pin(pinned, "calibration_plan_hash")["value"][:12]


def test_validation_gate_tally_claims_rederive_from_source(
    load_pinned_values: Any,
) -> None:
    """Bind the staged-gate pass tally to a fresh run of run_all_gates.

    03_results.md / Validation gates: "{{TOTAL_GATES_PASSED}} of
    {{TOTAL_GATES_RUN}} staged-gate evaluations passing (run_all_gates x
    {{EXAMPLE_METHOD_COUNT}} methods x {{DSL_GATE_COUNT}} gates each)". Both
    worked examples pass every gate, so run_all_gates does not short-circuit:
    2 methods x 4 gates = 8 run, all 8 pass.
    """

    pinned = load_pinned_values("template_methods_paper")

    total_run = 0
    total_passed = 0
    for method in all_example_methods():
        results = run_all_gates(method)
        total_run += len(results)
        total_passed += sum(1 for gate in results if gate.passed)

    _assert_pin_matches(_pin(pinned, "total_gates_run"), total_run)
    _assert_pin_matches(_pin(pinned, "total_gates_passed"), total_passed)


def test_provenance_chain_claim_rederives_from_source(
    load_pinned_values: Any,
) -> None:
    """Bind the demonstration provenance-chain length to a fresh demo run.

    03_results.md / Provenance demonstration: a {{TRUST_CHAIN_LENGTH}}-record
    hash-chain (DECLARED -> CALIBRATED -> VERIFIED) whose verification the
    manuscript reports as {{TRUST_CHAIN_VERIFIED}}. We pin the length and
    additionally assert the live chain verifies (the load-bearing claim).
    """

    pinned = load_pinned_values("template_methods_paper")
    report = demo_chain_report()

    _assert_pin_matches(_pin(pinned, "trust_chain_length"), report["chain_length"])
    # The manuscript's rendered {{TRUST_CHAIN_VERIFIED}} = Yes; assert it live.
    assert report["verified"] is True


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pins -- not that the comparison is a no-op. Exercises
    both the string (hash) branch and the numeric (count) branch.
    """

    pinned = load_pinned_values("template_methods_paper")

    # Numeric branch: perturb a pinned count.
    count_entry = dict(_pin(pinned, "pbs_step_count"))
    observed_count = count_entry["value"]
    count_entry["value"] = observed_count + 1
    with pytest.raises(AssertionError):
        _assert_pin_matches(count_entry, observed_count)

    # String branch: flip one hex char of a pinned SHA-256 digest.
    hash_entry = dict(_pin(pinned, "pbs_plan_hash"))
    observed_hash = hash_entry["value"]
    mutated = ("f" if observed_hash[0] != "f" else "0") + observed_hash[1:]
    hash_entry["value"] = mutated
    with pytest.raises(AssertionError):
        _assert_pin_matches(hash_entry, observed_hash)
