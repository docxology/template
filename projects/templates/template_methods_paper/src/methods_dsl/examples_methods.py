"""Two worked example methods used by the manuscript, tests, and analysis script.

The first is wet-lab-flavored (in BPL's domain, but an original example — not
a copy of BPL's shipped ``PrepareLBMedia`` protocol). The second is a
non-biology controlled procedure (instrument calibration), demonstrating that
the DSL's vocabulary generalizes beyond wet-lab protocols to any controlled
system, as the project's design intends.
"""

from __future__ import annotations

from .model import Method, Parameter, Resource, Step
from .units import Quantity
from .vocabulary import StepKind, Target


def pbs_preparation_method() -> Method:
    """A phosphate-buffered-saline preparation protocol (manual bench work)."""
    return Method(
        name="PBSPreparation",
        version="1.0",
        target=Target.HUMAN,
        parameters=(Parameter("final_volume", Quantity(1000.0, "mL"), "Target solution volume"),),
        resources=(
            Resource("WaterReservoir", kind="solvent", capacity=Quantity(2.0, "L")),
            Resource("PBSTabletStock", kind="reagent"),
            Resource("MixingBeaker", kind="container", capacity=Quantity(1.0, "L")),
        ),
        steps=(
            Step(
                step_id=1,
                name="Add water to beaker",
                kind=StepKind.ADD,
                target=Target.HUMAN,
                parameters=(Parameter("volume", Quantity(800.0, "mL")),),
                expected_duration=Quantity(2.0, "min"),
            ),
            Step(
                step_id=2,
                name="Add PBS tablet",
                kind=StepKind.ADD,
                target=Target.HUMAN,
                parameters=(Parameter("count", Quantity(1.0, "count")),),
                depends_on=(1,),
            ),
            Step(
                step_id=3,
                name="Mix until dissolved",
                kind=StepKind.MIX,
                target=Target.HUMAN,
                expected_duration=Quantity(10.0, "min"),
                depends_on=(2,),
            ),
            Step(
                step_id=4,
                name="Top up to final volume",
                kind=StepKind.ADD,
                target=Target.HUMAN,
                parameters=(Parameter("volume", Quantity(200.0, "mL")),),
                depends_on=(3,),
            ),
            Step(
                step_id=5,
                name="Validate solution clarity and pH range",
                kind=StepKind.VALIDATE,
                target=Target.HUMAN,
                depends_on=(4,),
            ),
        ),
    )


def sensor_calibration_method() -> Method:
    """An instrument-calibration controlled procedure (mixed automated + human steps)."""
    return Method(
        name="SensorCalibrationSweep",
        version="1.0",
        target=Target.AUTOMATED,
        resources=(
            Resource("ReferenceSource", kind="instrument"),
            Resource("DeviceUnderTest", kind="instrument"),
        ),
        steps=(
            Step(
                step_id=1,
                name="Record reference baseline reading",
                kind=StepKind.MEASURE,
                target=Target.AUTOMATED,
                expected_duration=Quantity(30.0, "s"),
            ),
            Step(
                step_id=2,
                name="Compute calibration offset",
                kind=StepKind.COMPUTE,
                target=Target.AUTOMATED,
                depends_on=(1,),
            ),
            Step(
                step_id=3,
                name="Operator sign-off on computed offset",
                kind=StepKind.ANNOTATE,
                target=Target.HUMAN,
                depends_on=(2,),
            ),
            Step(
                step_id=4,
                name="Validate calibration within tolerance",
                kind=StepKind.VALIDATE,
                target=Target.AUTOMATED,
                depends_on=(3,),
            ),
        ),
    )


def all_example_methods() -> tuple[Method, ...]:
    """Every example method, in the fixed order the script and manuscript report them."""
    return (pbs_preparation_method(), sensor_calibration_method())
