"""Regression pins for the deterministic SIA self-improvement harness.

Manuscript: projects/templates/template_sia/manuscript/03_results.md.

This exemplar is a *self-improvement* harness: a Meta -> Target -> Feedback
loop that, under fixture replay (``sia.live: false`` in manuscript/config.yaml,
the CI default), advances a target agent across three generations and records
an accuracy metric each time. The load-bearing manuscript claims are the
self-refinement signal itself -- accuracy climbs 0.5000 -> 0.6667 -> 0.8333
over three generations, a final-minus-first delta of 0.3333, and a final
injected token ``accuracy=0.8333 (n=6)``. These pins bind those exact numbers
to the source: each value is re-derived by running the real
``infrastructure.sia.run_sia_loop`` in fixture-replay mode (which copies the
recorded per-generation fixtures into a fresh output tree and reads each
``results.json`` verbatim via the real ``EvaluationResult`` contract) -- never
by hand-copying a rendered manuscript token, and never in a live /
non-deterministic mode.

Fixture replay executes no generated agent code and calls no external LLM, in
line with the exemplar's determinism contract and the repo no-mock policy: the
run uses real deterministic objects and the real loop state machine only.
"""

from __future__ import annotations

import importlib
import importlib.util
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_sia"

_PKG_ALIAS = "_sia_src"

# This exemplar's own src/loop.py does an absolute ``from src.artifact_manifest
# import ...`` (assuming its own package is importable as the bare name
# ``src``). The scoped finder below resolves exactly that -- and only that --
# from this project's own directory, for the duration of the load only.
_TOP_LEVEL = frozenset({"src"})


class _SrcScopedFinder(MetaPathFinder):
    """Resolve this exemplar's bare ``src`` name from its own directory only.

    Installed on ``sys.meta_path`` only while loading this project's package
    (never left permanently -- see ``_load_absolute_submodules``), so the
    exemplar's absolute ``from src.artifact_manifest import ...`` resolves to
    *this* project's ``src/`` tree without a global ``sys.path`` entry that
    would collide with another exemplar's top-level packages of the same name.
    """

    def find_spec(
        self,
        fullname: str,
        path: Any = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if fullname.split(".")[0] not in _TOP_LEVEL:
            return None
        return PathFinder.find_spec(fullname, [str(PROJECT_ROOT)], target)


def _load_absolute_submodules(*dotted_names: str) -> tuple[ModuleType, ...]:
    """Load this exemplar's ``src`` package (plus the named submodules) under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    An earlier version of this loader permanently inserted ``PROJECT_ROOT``
    onto ``sys.path`` (with no cleanup) so the exemplar's own absolute
    ``from src.artifact_manifest import ...`` would resolve -- but that left a
    real, uncleaned ``sys.modules['src']`` entry (this project's) for the rest
    of the pytest session, which then silently hijacked
    ``template_search_project``'s own absolute ``from src.config import ...``
    once both exemplars' regression tests collected together (whichever
    project's ``src`` got cached into ``sys.modules`` first wins for everyone
    else, since the cache is checked before ``sys.meta_path``). Using a
    temporarily-installed scoped finder (removed, with ``sys.modules``
    cleanup, in every case) avoids leaking either the path entry or the cache
    entry.
    """

    if _PKG_ALIAS in sys.modules:
        return tuple(importlib.import_module(f"{_PKG_ALIAS}.{dotted}") for dotted in dotted_names)

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))  # needed for `infrastructure.*`; shared-safe, no top-level collision

    pre_existing_src = {key: mod for key, mod in sys.modules.items() if key == "src" or key.startswith("src.")}
    finder = _SrcScopedFinder()
    sys.meta_path.insert(0, finder)
    try:
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
        return tuple(importlib.import_module(f"{_PKG_ALIAS}.{dotted}") for dotted in dotted_names)
    finally:
        sys.meta_path.remove(finder)
        for key in [k for k in sys.modules if (k == "src" or k.startswith("src.")) and k not in pre_existing_src]:
            del sys.modules[key]
        sys.modules.update(pre_existing_src)


# The project's own thin orchestrator (src/loop.py) re-exports the harness
# entry points from scripts/sia_loop_impl.py, which in turn drive the real
# infrastructure.sia loop. Re-deriving through this surface binds the pins to
# the exemplar's actual public API, not a private shortcut.
(_loop_mod,) = _load_absolute_submodules("loop")
build_run_config = _loop_mod.build_run_config
run_sia_loop_project = _loop_mod.run_sia_loop_project

# The infrastructure loop + config live one import below; use them directly to
# run into an isolated output tree without touching the committed run.
from infrastructure.sia import RunConfig, run_sia_loop  # noqa: E402


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def replay_evaluations(tmp_path_factory: pytest.TempPathFactory) -> list[Any]:
    """Re-derive the three-generation fixture-replay metrics from the real loop.

    Runs ``infrastructure.sia.run_sia_loop`` with the exemplar's own config
    (``build_run_config``) but redirected to an isolated output directory, so
    the re-derivation is a genuine fresh run and never reads the committed
    ``output/runs/run_1/run_summary.json``. ``live`` is forced ``False`` to pin
    the deterministic fixture-replay path the manuscript describes.
    """

    base = build_run_config(PROJECT_ROOT, live=False)
    assert base.live is False, "regression pins must use deterministic fixture replay"
    isolated_out = tmp_path_factory.mktemp("sia_replay")
    config = RunConfig(
        task_dir=base.task_dir,
        output_dir=isolated_out,
        run_id=base.run_id,
        max_generations=base.max_generations,
        live=False,
        fixtures_dir=base.fixtures_dir,
        target_timeout_sec=base.target_timeout_sec,
        llm_model=base.llm_model,
    )
    artifacts = run_sia_loop(config)
    evaluations = [artifact.evaluation for artifact in artifacts]
    assert all(ev is not None for ev in evaluations), "every replayed generation must evaluate"
    return evaluations


def test_generation_metric_progression_claims_rederive_from_source(
    load_pinned_values: Any,
    replay_evaluations: list[Any],
) -> None:
    """Bind the fixture-replay metrics table headline numbers to a fresh source run.

    03_results.md / SIA generation metrics (fixture replay) table + final-token
    prose. The self-refinement signal (accuracy 0.5000 -> ... -> 0.8333 across
    three generations, n=6) is what this exemplar exists to demonstrate.
    """

    pinned = load_pinned_values("template_sia")
    evaluations = replay_evaluations

    # Loop length: the three-generation Meta -> Target -> Feedback cycle.
    _assert_pin_matches(_pin(pinned, "generation_count"), len(evaluations))

    # Seed baseline (generation 1) and final (generation 3) accuracy.
    _assert_pin_matches(_pin(pinned, "first_generation_accuracy"), evaluations[0].metric_value)
    _assert_pin_matches(_pin(pinned, "final_generation_accuracy"), evaluations[-1].metric_value)

    # Final sample count backing the reported accuracy=0.8333 (n=6) token.
    _assert_pin_matches(_pin(pinned, "final_generation_n_samples"), evaluations[-1].n_samples)


def test_self_improvement_delta_claim_rederives_from_source(
    load_pinned_values: Any,
    replay_evaluations: list[Any],
) -> None:
    """Bind the self-improvement delta (final - first) to a fresh source run.

    03_results.md / 'Metric delta (final - first generation): 0.3333'. Computed
    from the real loop's first and last evaluation.metric_value, not read from
    the rendered SIA_METRIC_DELTA token.
    """

    pinned = load_pinned_values("template_sia")
    evaluations = replay_evaluations

    delta = evaluations[-1].metric_value - evaluations[0].metric_value
    _assert_pin_matches(_pin(pinned, "metric_delta_final_minus_first"), delta)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_sia")
    entry = dict(_pin(pinned, "final_generation_accuracy"))
    observed = entry["value"]
    entry["value"] = observed + 0.5  # perturb the pinned ground truth well beyond tolerance

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
