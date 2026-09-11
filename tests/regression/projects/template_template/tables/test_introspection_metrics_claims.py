"""Regression pins for the autopoietic meta-template's self-introspection metrics.

Manuscript: projects/templates/template_template/manuscript/ (abstract,
introduction, architecture, results, quality, scalability, appendix-docs, and
manuscript/AGENTS.md token table).

This exemplar is *reflexive*: it introspects the LIVE repository (the
``infrastructure/`` subdirectory roster, the ``pipeline.yaml`` DAG, and
``PUBLIC_PROJECT_NAMES``) and injects the resulting numbers straight into its
own manuscript as ``${token}`` values. The pins below bind those exact claims
to the real source functions:

- ``pipeline_stages_declared`` / ``_default_full`` / ``_core_only`` come from
  the frozen ``infrastructure/core/pipeline/pipeline.yaml`` DAG structure and
  are pinned by AGENTS.md as the literals ``(14)`` / ``(10)`` / ``(8)`` — hard
  structural claims, tolerance 0.
- ``public_exemplar_roster_count`` is the size of the confidentiality-invariant
  public exemplar roster (``PUBLIC_PROJECT_NAMES``) that the manuscript renders
  via ``${public_exemplar_list}`` — a hard invariant, tolerance 0.
- ``module_count`` is the LIVE ``infrastructure/`` subdirectory count, the
  single most-cited introspection number in the manuscript. It legitimately
  drifts as the repo grows, so it carries an ``abs_tolerance`` band (per the
  exemplar's own convention in ``manuscript/AGENTS.md``: rotating layout facts
  defer to ``docs/_generated/COUNTS.md``) — wide enough to survive adding one
  infra module, tight enough to fail on a broken discovery or a large jump.

Every value is re-derived by calling the real
``template_template.core.introspection`` functions (and
``infrastructure.project.public_scope.public_project_names``) on the repo root
-- never by hand-copying a rendered ``${token}`` from the manuscript.

No mocks: real filesystem introspection of the live repository only, in line
with the repo no-mock policy.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_template"
_SRC = PROJECT_ROOT / "src" / "template_template"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))  # needed for ``infrastructure.*``

# SUBMODULAR-TEMPLATE-1: the exemplar package is a regular nested package
# (``src/template_template/``) whose subpackage modules import via absolute
# ``template_template.*`` paths, so the exemplar imports directly -- no
# project-unique alias or scoped meta-path finder is needed. The alias
# machinery existed only to resolve the pre-split flat layout's
# ``sys.modules['src']`` collision, which no longer applies: the repo conftest
# places every ``projects/*/src`` on ``sys.path`` and each exemplar owns a
# unique nested package name. Import the tested functions via the real
# absolute module paths.
assert _SRC.is_dir(), f"exemplar package missing: {_SRC}"
from template_template.core.introspection import (  # noqa: E402
    build_infrastructure_report,
    discover_infrastructure_modules,
)

# public_scope is plain infrastructure (no src-package collision), imported directly.
from infrastructure.project.public_scope import public_project_names  # noqa: E402


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def report() -> Any:
    """Re-derive the live infrastructure report exactly as build_manuscript_metrics_dict does."""

    return build_infrastructure_report(REPO_ROOT)


@pytest.mark.timeout(30)
def test_pipeline_dag_stage_counts_rederive_from_yaml(
    load_pinned_values: Any,
    report: Any,
) -> None:
    """Bind the frozen pipeline.yaml DAG stage counts to a fresh source read.

    manuscript/AGENTS.md token table pins the literals (14) / (10) / (8);
    ${pipeline_stages_declared} / ${pipeline_stages_default_full} /
    ${pipeline_stages_core_only} are injected across the abstract, introduction,
    architecture, documentation, security, and results sections.

    The ``report`` fixture calls ``build_infrastructure_report``, which does a
    full ``repo_root.rglob("*.py")`` walk (~17k files across this monorepo) —
    measured ~15s standalone, comfortably past the repo's default 10s pytest
    timeout. Override to 30s for this one test rather than the whole tier.
    """

    pinned = load_pinned_values("template_template")

    _assert_pin_matches(
        _pin(pinned, "pipeline_stages_declared"),
        report.pipeline_stages_declared,
    )
    _assert_pin_matches(
        _pin(pinned, "pipeline_stages_default_full"),
        report.pipeline_stages_default_full,
    )
    _assert_pin_matches(
        _pin(pinned, "pipeline_stages_core_only"),
        report.pipeline_stages_core_only,
    )


def test_public_exemplar_roster_count_rederives_from_source(
    load_pinned_values: Any,
) -> None:
    """Bind the confidentiality-invariant public exemplar roster size.

    The manuscript renders the full roster as ${public_exemplar_list} (abstract,
    introduction, architecture, appendix-exemplars). ``public_project_names`` is
    the single source of truth for which names may reach the public DOI, so its
    length is a hard invariant (tolerance 0). The stale appendix prose 'currently
    nine workspaces' is deliberately NOT pinned — it is not source-derived.
    """

    pinned = load_pinned_values("template_template")

    _assert_pin_matches(
        _pin(pinned, "public_exemplar_roster_count"),
        len(public_project_names(REPO_ROOT)),
    )


def test_live_module_count_rederives_within_drift_band(
    load_pinned_values: Any,
) -> None:
    """Bind the live infrastructure module count with a growth-tolerant band.

    ${module_count} is the most-cited introspection number in the manuscript
    (abstract, introduction, architecture, results, quality, scalability,
    infrastructure-modules, ai-collaboration, appendix-docs). It is a live count
    that drifts as the repo grows, so the pin carries abs_tolerance (see the pin
    JSON) — enough to survive one added infra module, tight enough to catch a
    broken discovery (0, a halving) or a large structural jump.
    """

    pinned = load_pinned_values("template_template")

    _assert_pin_matches(
        _pin(pinned, "module_count"),
        len(discover_infrastructure_modules(REPO_ROOT)),
    )


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op. Uses the
    frozen tolerance-0 ``pipeline_stages_declared`` pin so a +1 perturbation is
    guaranteed to breach the (zero) tolerance.
    """

    pinned = load_pinned_values("template_template")
    entry = dict(_pin(pinned, "pipeline_stages_declared"))
    observed = entry["value"]
    entry["value"] = observed + 1  # perturb the pinned ground truth

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
