"""Stage outcomes serialize through two different shapes, and both are contracts.

Investigating the CI failures showed the producer must emit **both** shapes for
different consumers, which is why the rule is per field path and not a blanket
"never use ``asdict``":

* **Stage rows** carry a nested ``outcome`` mapping that must contain *every*
  ``StageOutcome`` field, because ``results_from_payload`` reconstructs the type
  from the field set. ``asdict`` is required there.
* **A ``RunResult.outcomes`` list** is compared against
  ``StageOutcome.to_dict()``, which omits an unset ``condition``. Producing it
  with ``asdict`` emitted ``condition: null`` for untyped outcomes and the
  summary worker refused the whole multi-project aggregate -- the failure that
  made two CI shards red.

The consumer-level proof lives in the existing tests that call
``write_summary_reports`` for real (``test_multi_project_custody_review.py`` and
``test_multi_project_cli.py``); these tests pin the unit-level properties that
decide the producer's shape and the reason the field must stay a real field.
"""

from __future__ import annotations

import dataclasses

from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus

_PRE_CHANGE_KEYS = {
    "stage_key",
    "status",
    "child_exit_code",
    "diagnostic",
    "attempt_count",
    "reason",
    "receipt_validated",
    "retryable",
    "attempt_exit_codes",
    "in_process_completed",
}


def test_to_dict_omits_an_unset_condition_and_keeps_a_set_one() -> None:
    """The shape `RunResult.outcomes` is compared against."""
    untyped = StageOutcome("render_pdf", StageStatus.SUCCEEDED, 0)
    assert set(untyped.to_dict()) == _PRE_CHANGE_KEYS
    assert "condition" not in untyped.to_dict()
    typed = StageOutcome("render_pdf", StageStatus.TIMED_OUT, 124, condition="unattributed_exit_124")
    assert typed.to_dict()["condition"] == "unattributed_exit_124"


def test_asdict_emits_every_field_and_is_required_for_stage_rows() -> None:
    """The shape `results_from_payload` reconstructs from -- field set equality."""
    untyped = StageOutcome("render_pdf", StageStatus.SUCCEEDED, 0)
    emitted = dataclasses.asdict(untyped)
    assert "condition" in emitted
    assert set(emitted) == _PRE_CHANGE_KEYS | {"condition"}
    assert set(emitted) == {field.name for field in dataclasses.fields(StageOutcome)}


def test_replace_preserves_the_typed_condition() -> None:
    """Pins the property that ruled out hiding the field from `asdict`.

    A non-field attribute would be invisible to `replace`, and
    `attach_stage_outcome` rebuilds outcomes with `replace(child, ...)`, so that
    fix would have dropped the typed cause on exactly the paths that re-key
    outcomes -- worse than the bug it fixed.
    """
    typed = StageOutcome("render_pdf", StageStatus.TIMED_OUT, 124, condition="custody_refusal")
    assert dataclasses.replace(typed, stage_key="output_validation").condition == "custody_refusal"
