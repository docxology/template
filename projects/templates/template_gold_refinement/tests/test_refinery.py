"""Tests for src.refinery — refinery pipeline stages."""

from __future__ import annotations

import pytest

from purity import NINE_NINES_PURITY
from refinery import (
    CANONICAL_STAGES,
    RefinementStage,
    run_refinery,
    stage_by_name,
    stage_by_order,
)


class TestCanonicalStages:
    def test_five_stages(self):
        assert len(CANONICAL_STAGES) == 5

    def test_stage_names(self):
        names = [s.name for s in CANONICAL_STAGES]
        assert names == ["ore", "smelting", "assaying", "cupellation", "certification"]

    def test_stage_orders(self):
        for i, stage in enumerate(CANONICAL_STAGES):
            assert stage.order == i + 1

    def test_monotone_purity(self):
        purities = [CANONICAL_STAGES[0].input_purity] + [s.output_purity for s in CANONICAL_STAGES]
        for i in range(1, len(purities)):
            assert purities[i] > purities[i - 1]

    def test_final_stage_is_nine_nines(self):
        assert CANONICAL_STAGES[-1].output_purity == NINE_NINES_PURITY

    def test_first_stage_input_is_low(self):
        assert CANONICAL_STAGES[0].input_purity == 0.10

    def test_stage_input_matches_previous_output(self):
        for i in range(1, len(CANONICAL_STAGES)):
            assert CANONICAL_STAGES[i].input_purity == CANONICAL_STAGES[i - 1].output_purity


class TestRunRefinery:
    def test_result_has_correct_stages(self):
        result = run_refinery()
        assert result.stage_count == 5
        assert len(result.stages) == 5

    def test_final_purity(self):
        result = run_refinery()
        assert result.final_purity == NINE_NINES_PURITY

    def test_final_karat(self):
        result = run_refinery()
        assert result.final_karat.karat == 24
        assert "nine-nines" in result.final_karat.label

    def test_total_purity_gain(self):
        result = run_refinery()
        assert pytest.approx(result.total_purity_gain, abs=1e-10) == NINE_NINES_PURITY - 0.10

    def test_is_nine_nines_certified(self):
        result = run_refinery()
        assert result.is_nine_nines_certified is True

    def test_stage_labels(self):
        result = run_refinery()
        labels = result.stage_labels
        assert len(labels) == 5
        assert "ore" in labels[0]
        assert "certification" in labels[4]

    def test_purity_sequence(self):
        result = run_refinery()
        seq = result.purity_sequence
        assert len(seq) == 6  # input to first + output of each
        assert seq[0] == 0.10
        assert seq[-1] == NINE_NINES_PURITY

    def test_purity_sequence_empty_stages(self):
        """RefineryResult with empty stages tuple returns empty purity_sequence."""
        from refinery import RefineryResult, KaratGrade
        from purity import karat_for_purity
        result = RefineryResult(
            stages=(),
            final_purity=0.999999999,
            final_karat=karat_for_purity(0.999999999),
            total_purity_gain=0.9,
        )
        assert result.purity_sequence == ()

    def test_empty_pipeline_raises(self):
        with pytest.raises(ValueError, match="at least one stage"):
            run_refinery(stages=())

    def test_non_monotone_pipeline_raises(self):
        bad_stages = (
            RefinementStage(
                name="a", metallurgical_operation="op", manuscript_operation="mop",
                input_purity=0.5, output_purity=0.3, order=1,
            ),
            RefinementStage(
                name="b", metallurgical_operation="op", manuscript_operation="mop",
                input_purity=0.3, output_purity=0.9, order=2,
            ),
        )
        with pytest.raises(ValueError, match="must increase monotonically"):
            run_refinery(stages=bad_stages)

    def test_wrong_order_raises(self):
        bad_stages = (
            RefinementStage(
                name="a", metallurgical_operation="op", manuscript_operation="mop",
                input_purity=0.1, output_purity=0.5, order=2,
            ),
        )
        with pytest.raises(ValueError, match="Stage order mismatch"):
            run_refinery(stages=bad_stages)


class TestRefinementStage:
    def test_karat_grade(self):
        stage = CANONICAL_STAGES[0]
        assert stage.karat_grade.karat == 9

    def test_purity_gain(self):
        stage = CANONICAL_STAGES[0]
        assert pytest.approx(stage.purity_gain, abs=1e-6) == 0.375 - 0.10

    def test_label_format(self):
        stage = CANONICAL_STAGES[0]
        assert stage.label.startswith("1. ore")


class TestStageLookup:
    def test_by_name_ore(self):
        stage = stage_by_name("ore")
        assert stage.order == 1

    def test_by_name_case_insensitive(self):
        stage = stage_by_name("Cupellation")
        assert stage.order == 4

    def test_by_name_not_found(self):
        with pytest.raises(KeyError, match="No refinement stage named"):
            stage_by_name("nonexistent")

    def test_by_order_1(self):
        stage = stage_by_order(1)
        assert stage.name == "ore"

    def test_by_order_5(self):
        stage = stage_by_order(5)
        assert stage.name == "certification"

    def test_by_order_not_found(self):
        with pytest.raises(KeyError, match="No refinement stage with order"):
            stage_by_order(99)
