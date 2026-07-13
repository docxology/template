"""Tests for src.purity — karat grading and purity computation."""

from __future__ import annotations

import pytest

from purity import (
    KARAT_GRADES,
    NINE_NINES_PURITY,
    KaratGrade,
    assert_monotone_increase,
    format_purity,
    karat_for_purity,
    purity_to_nines,
    PurityVector,
)


class TestPurityVector:
    def test_preserves_independent_dimensions(self):
        vector = PurityVector(1.0, 0.75, 1.0, 0.9)
        assert vector.weakest_dimension == ("claim_support", 0.75)
        assert not vector.all_complete
        assert vector.as_dict()["figure_quality"] == 0.9

    def test_all_complete(self):
        assert PurityVector(1.0, 1.0, 1.0, 1.0).all_complete

    def test_rejects_out_of_bounds_dimension(self):
        with pytest.raises(ValueError, match=r"must be in \[0, 1\]"):
            PurityVector(1.0, 1.1, 1.0, 1.0)


class TestKaratForPurity:
    def test_below_9k(self):
        grade = karat_for_purity(0.10)
        assert grade.karat == 0
        assert "below 9K" in grade.label

    def test_9k(self):
        grade = karat_for_purity(0.375)
        assert grade.karat == 9

    def test_18k(self):
        grade = karat_for_purity(0.75)
        assert grade.karat == 18

    def test_22k(self):
        grade = karat_for_purity(0.9167)
        assert grade.karat == 22

    def test_24k(self):
        grade = karat_for_purity(0.999)
        assert grade.karat == 24

    def test_nine_nines(self):
        grade = karat_for_purity(NINE_NINES_PURITY)
        assert grade.karat == 24
        assert "nine-nines" in grade.label

    def test_between_grades_rounds_down(self):
        # 0.60 is above 14K (0.585) but below 18K (0.750)
        grade = karat_for_purity(0.60)
        assert grade.karat == 14

    def test_invalid_purity_negative(self):
        with pytest.raises(ValueError, match="purity must be in"):
            karat_for_purity(-0.1)

    def test_invalid_purity_above_one(self):
        with pytest.raises(ValueError, match="purity must be in"):
            karat_for_purity(1.5)

    def test_zero_purity(self):
        grade = karat_for_purity(0.0)
        assert grade.karat == 0


class TestPurityToNines:
    def test_zero(self):
        assert purity_to_nines(0.0) == 0

    def test_one_nine(self):
        assert purity_to_nines(0.9) == 1

    def test_two_nines(self):
        assert purity_to_nines(0.99) == 2

    def test_three_nines(self):
        assert purity_to_nines(0.999) == 3

    def test_nine_nines(self):
        assert purity_to_nines(NINE_NINES_PURITY) == 9


class TestFormatPurity:
    def test_low_purity(self):
        result = format_purity(0.375)
        assert "37.50%" in result

    def test_mid_purity(self):
        result = format_purity(0.75)
        assert "75.00%" in result

    def test_high_purity(self):
        result = format_purity(0.999)
        assert "99.900%" in result

    def test_nine_nines(self):
        result = format_purity(NINE_NINES_PURITY)
        assert "nine-nines" in result


class TestAssertMonotoneIncrease:
    def test_strictly_increasing(self):
        assert assert_monotone_increase([0.1, 0.3, 0.5, 0.9]) is True

    def test_single_element(self):
        assert assert_monotone_increase([0.5]) is True

    def test_empty(self):
        assert assert_monotone_increase([]) is True

    def test_not_increasing(self):
        with pytest.raises(ValueError, match="must increase monotonically"):
            assert_monotone_increase([0.5, 0.3])

    def test_equal_not_allowed(self):
        with pytest.raises(ValueError, match="must increase monotonically"):
            assert_monotone_increase([0.5, 0.5])


class TestKaratGrade:
    def test_percentage_property(self):
        grade = KaratGrade(karat=18, purity=0.75, label="18K")
        assert grade.percentage == 75.0

    def test_nines_property(self):
        grade = KaratGrade(karat=24, purity=0.999, label="24K")
        assert grade.nines == 3

    def test_nines_property_nine_nines(self):
        """KaratGrade.nines at nine-nines purity should count many 9s (loop exhausted without break)."""
        grade = KaratGrade(karat=24, purity=NINE_NINES_PURITY, label="24K (nine-nines certified)")
        # At 99.9999999% the leading digit pattern has many 9s
        assert grade.nines >= 9

    def test_nines_property_low_purity(self):
        """KaratGrade.nines at low purity (e.g. 37.5%) is 0."""
        grade = KaratGrade(karat=9, purity=0.375, label="9K")
        assert grade.nines == 0


class TestKaratGradesConstant:
    def test_all_standard_grades_present(self):
        expected = {9, 10, 12, 14, 18, 20, 22, 23, 24}
        assert set(KARAT_GRADES.keys()) == expected

    def test_24k_is_999(self):
        assert KARAT_GRADES[24] == 0.999

    def test_9k_is_375(self):
        assert KARAT_GRADES[9] == 0.375
