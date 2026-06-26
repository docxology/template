"""Property-based tests for monotone purity across refinery stages.

Uses Hypothesis to generate random strictly-increasing purity sequences
and validates that the refinery pipeline and purity utilities handle
them correctly.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from purity import (
    assert_monotone_increase,
    karat_for_purity,
    purity_to_nines,
)
from refinery import CANONICAL_STAGES, run_refinery


class TestMonotoneIncreaseProperty:
    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, exclude_min=True, allow_nan=False),
            min_size=2,
            max_size=20,
        )
    )
    @settings(max_examples=100)
    def test_monotone_sequence_accepted(self, seq):
        # If the sequence happens to be strictly increasing, it should pass
        is_increasing = all(seq[i] < seq[i + 1] for i in range(len(seq) - 1))
        if is_increasing:
            assert assert_monotone_increase(seq) is True

    @given(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=2,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_non_increasing_raises(self, seq):
        is_increasing = all(seq[i] < seq[i + 1] for i in range(len(seq) - 1))
        if not is_increasing:
            with pytest.raises(ValueError, match="monotonically"):
                assert_monotone_increase(seq)


class TestCanonicalPipelineProperty:
    def test_canonical_pipeline_is_monotone(self):
        """The canonical 5-stage pipeline must always be strictly monotone."""
        result = run_refinery()
        seq = list(result.purity_sequence)
        for i in range(1, len(seq)):
            assert seq[i] > seq[i - 1], (
                f"Stage {i}: {seq[i]} <= {seq[i - 1]}"
            )

    def test_canonical_pipeline_final_is_nine_nines(self):
        """The canonical pipeline always reaches nine-nines."""
        result = run_refinery()
        assert result.final_purity >= 0.999999999

    def test_each_stage_input_matches_previous_output(self):
        """Stage i input must equal stage i-1 output."""
        for i in range(1, len(CANONICAL_STAGES)):
            assert (
                CANONICAL_STAGES[i].input_purity
                == CANONICAL_STAGES[i - 1].output_purity
            )


class TestKaratGradeProperty:
    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200)
    def test_karat_grade_in_range(self, purity):
        grade = karat_for_purity(purity)
        assert 0 <= grade.karat <= 24
        assert 0.0 <= grade.purity <= 1.0

    @given(
        st.floats(min_value=0.375, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_high_purity_has_karat(self, purity):
        grade = karat_for_purity(purity)
        assert grade.karat >= 9, f"Purity {purity} should be at least 9K"

    @given(
        st.floats(min_value=0.999, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_near_one_is_24k(self, purity):
        grade = karat_for_purity(purity)
        assert grade.karat == 24


class TestNinesProperty:
    @given(
        st.floats(min_value=0.9, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_nines_non_negative(self, purity):
        assert purity_to_nines(purity) >= 0

    def test_nines_monotone_with_purity(self):
        """More nines means higher purity."""
        assert purity_to_nines(0.9) < purity_to_nines(0.99)
        assert purity_to_nines(0.99) < purity_to_nines(0.999)
        assert purity_to_nines(0.999) < purity_to_nines(0.9999)
