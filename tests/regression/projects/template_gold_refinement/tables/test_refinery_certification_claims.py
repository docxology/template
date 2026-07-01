"""Regression pins for the metallurgical gold-refining exemplar.

Manuscript: projects/templates/template_gold_refinement/manuscript/03_results.md.

This exemplar frames manuscript composition as a gold refinery: raw ore prose is
smelted, assayed, cupellated, and finally certified to "nine-nines" purity
(0.999999999). The frame is load-bearing, not decorative — every headline number
in the results section is emitted by a real source function, and these pins bind
those exact numbers back to the source:

  * ``src.refinery.run_refinery`` owns the 5-stage pipeline, its final nine-nines
    purity, and (via ``src.purity.purity_to_nines``) the "Nines count: 9" claim.
  * ``src.formalisms.formalism_count`` owns the "7 source-owned formalisms" claim.
  * ``src.evidence.build_evidence_registry`` owns the project-local claim-support
    assay ("9 supported claims out of 9 total"), AST-verifying each claim's
    evidence source against the real project files.

Each value is re-derived by calling the same function the manuscript-variable
generator (``src/manuscript_variables.py``) calls — never by hand-copying a
number from the rendered manuscript.

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
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_gold_refinement"

_PKG_ALIAS = "_gold_refinement_src"


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


run_refinery = _import_submodule("refinery").run_refinery
purity_to_nines = _import_submodule("purity").purity_to_nines
formalism_count = _import_submodule("formalisms").formalism_count
load_gold_refinement_config = _import_submodule("config").load_gold_refinement_config
build_evidence_registry = _import_submodule("evidence").build_evidence_registry


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def refinery_result() -> Any:
    """Re-derive the refinery pipeline exactly as manuscript_variables.generate_variables does."""

    return run_refinery()


@pytest.fixture(scope="module")
def evidence_registry() -> Any:
    """Re-derive the project-local claim-support assay from config + project files."""

    config = load_gold_refinement_config(PROJECT_ROOT)
    return build_evidence_registry(config, PROJECT_ROOT)


def test_refinery_certification_claims_rederive_from_source(
    load_pinned_values: Any,
    refinery_result: Any,
) -> None:
    """Bind the refinery headline (stage count, nine-nines purity, nines count) to a fresh source run.

    03_results.md opening + Final certification: "across 5 stages, reaching final
    purity of 99.9999999% (nine-nines)" and "Nines count: 9".
    """

    pinned = load_pinned_values("template_gold_refinement")

    # Five canonical stages: ore, smelting, assaying, cupellation, certification.
    _assert_pin_matches(
        _pin(pinned, "refinery_num_stages"),
        refinery_result.stage_count,
    )

    # Terminal certified purity is exactly nine-nines (0.999999999).
    _assert_pin_matches(
        _pin(pinned, "refinery_final_purity"),
        refinery_result.final_purity,
    )

    # The manuscript's "Nines count" is derived from the final purity, not stored.
    _assert_pin_matches(
        _pin(pinned, "refinery_final_nines"),
        purity_to_nines(refinery_result.final_purity),
    )


def test_formalism_count_claim_rederives_from_source(load_pinned_values: Any) -> None:
    """Bind the "7 source-owned formalisms" claim to the live registry.

    03_results.md / Formalism traceability: "The registry currently exposes 7
    source-owned formalisms."
    """

    pinned = load_pinned_values("template_gold_refinement")
    _assert_pin_matches(_pin(pinned, "formalism_count"), formalism_count())


def test_claim_support_assay_claims_rederive_from_source(
    load_pinned_values: Any,
    evidence_registry: Any,
) -> None:
    """Bind the project-local claim-support assay counts to a fresh source assay.

    03_results.md / Contribution claims + Claim-evidence assay: "reports 9
    supported claims out of 9 total claims". build_evidence_registry AST-verifies
    each claim's evidence source against the real project files, so this pin
    catches both a claim being added/removed and an evidence pointer going stale.
    """

    pinned = load_pinned_values("template_gold_refinement")

    _assert_pin_matches(
        _pin(pinned, "claim_support_supported"),
        evidence_registry.supported_claims,
    )
    _assert_pin_matches(
        _pin(pinned, "claim_support_total"),
        evidence_registry.total_claims,
    )


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_gold_refinement")
    entry = dict(_pin(pinned, "refinery_num_stages"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
