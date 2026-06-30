"""Pytest configuration for template_methods_paper tests."""

import os
import sys

# Force headless backend for matplotlib in tests (figures use it indirectly
# via infrastructure rendering helpers invoked from scripts/).
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ AND the repo root to path so the documented per-project pytest command
# works from a clean environment. The project pyproject's `pythonpath` is
# project-relative and omits the repo root, so without this the suite cannot import
# `infrastructure` (tests collect-error). The project lives at
# projects/templates/<name>/, so the repo root is three levels above ROOT.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
for _path in (REPO_ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import pytest  # noqa: E402

from src.methods_dsl.model import Method, Parameter, Resource, Step  # noqa: E402
from src.methods_dsl.units import Quantity  # noqa: E402
from src.methods_dsl.vocabulary import StepKind, Target  # noqa: E402

# Shared fixtures: minimal valid and deliberately-invalid Method objects.
# No mocks — every fixture is a real, fully-constructed Method.


@pytest.fixture
def linear_method() -> Method:
    """Three steps in a strict chain: 1 -> 2 -> 3."""
    return Method(
        name="LinearDemo",
        version="1.0",
        target=Target.HUMAN,
        steps=(
            Step(
                step_id=1,
                name="Add water",
                kind=StepKind.ADD,
                target=Target.HUMAN,
                parameters=(Parameter("volume", Quantity(10.0, "mL")),),
            ),
            Step(step_id=2, name="Mix", kind=StepKind.MIX, target=Target.HUMAN, depends_on=(1,)),
            Step(step_id=3, name="Validate", kind=StepKind.VALIDATE, target=Target.HUMAN, depends_on=(2,)),
        ),
        resources=(Resource("Beaker", kind="container", capacity=Quantity(1.0, "L")),),
    )


@pytest.fixture
def diamond_method() -> Method:
    """A diamond DAG: 1 -> {2, 3} -> 4, to exercise non-linear scheduling."""
    return Method(
        name="DiamondDemo",
        version="1.0",
        target=Target.AUTOMATED,
        steps=(
            Step(step_id=1, name="Start", kind=StepKind.MEASURE, target=Target.AUTOMATED),
            Step(step_id=2, name="Branch A", kind=StepKind.COMPUTE, target=Target.AUTOMATED, depends_on=(1,)),
            Step(step_id=3, name="Branch B", kind=StepKind.COMPUTE, target=Target.AUTOMATED, depends_on=(1,)),
            Step(step_id=4, name="Join", kind=StepKind.VALIDATE, target=Target.AUTOMATED, depends_on=(2, 3)),
        ),
    )


@pytest.fixture
def unknown_dependency_method() -> Method:
    """A method whose step 1 depends on a non-existent step_id (structural-gate failure).

    Construction itself succeeds — ``Step.__post_init__`` only rejects
    self-dependency, not unresolved cross-step references, so the structural
    gate is what catches this class of error.
    """
    return Method(
        name="DanglingDependency",
        version="1.0",
        target=Target.HUMAN,
        steps=(Step(step_id=1, name="Add", kind=StepKind.ADD, target=Target.HUMAN, depends_on=(99,)),),
    )


@pytest.fixture
def duplicate_step_id_method() -> Method:
    """Two steps sharing step_id=1 (structural-gate failure)."""
    return Method(
        name="DuplicateIds",
        version="1.0",
        target=Target.HUMAN,
        steps=(
            Step(step_id=1, name="First", kind=StepKind.ADD, target=Target.HUMAN),
            Step(step_id=1, name="Second", kind=StepKind.ADD, target=Target.HUMAN),
        ),
    )


@pytest.fixture
def unknown_unit_method() -> Method:
    """A resource whose capacity uses a unit outside the controlled vocabulary.

    Construction succeeds because ``Quantity`` does not validate its unit
    eagerly — ``dimension_of`` raises lazily on access — so the semantic gate
    is what catches this.
    """
    return Method(
        name="BadUnit",
        version="1.0",
        target=Target.HUMAN,
        resources=(Resource("Tank", kind="container", capacity=Quantity(1.0, "furlongs")),),
        steps=(Step(step_id=1, name="Add", kind=StepKind.ADD, target=Target.HUMAN),),
    )


@pytest.fixture
def cyclic_method() -> Method:
    """Two steps that depend on each other (plan-gate failure)."""
    return Method(
        name="Cyclic",
        version="1.0",
        target=Target.HUMAN,
        steps=(
            Step(step_id=1, name="A", kind=StepKind.ADD, target=Target.HUMAN, depends_on=(2,)),
            Step(step_id=2, name="B", kind=StepKind.ADD, target=Target.HUMAN, depends_on=(1,)),
        ),
    )


@pytest.fixture
def target_mismatch_method() -> Method:
    """A HUMAN-target method with one step requiring AUTOMATED (target-gate failure)."""
    return Method(
        name="TargetMismatch",
        version="1.0",
        target=Target.HUMAN,
        steps=(Step(step_id=1, name="Compute offset", kind=StepKind.COMPUTE, target=Target.HUMAN),),
    )
