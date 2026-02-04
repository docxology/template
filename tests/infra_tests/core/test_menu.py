"""Tests for menu utilities.

Tests the menu parsing and formatting functions using real data only.
No mocks - all tests use actual function calls with various inputs.
"""

import pytest

from infrastructure.core.menu import (MenuOption, format_menu,
                                      parse_choice_sequence)


class TestMenuOption:
    """Tests for MenuOption dataclass."""

    def test_menu_option_creation(self):
        """Test creating a MenuOption."""
        option = MenuOption(key="1", label="Run tests")

        assert option.key == "1"
        assert option.label == "Run tests"

    def test_menu_option_frozen(self):
        """Test that MenuOption is immutable."""
        option = MenuOption(key="1", label="Run tests")

        with pytest.raises(AttributeError):
            option.key = "2"

    def test_menu_option_equality(self):
        """Test MenuOption equality comparison."""
        opt1 = MenuOption(key="1", label="Test")
        opt2 = MenuOption(key="1", label="Test")
        opt3 = MenuOption(key="2", label="Test")

        assert opt1 == opt2
        assert opt1 != opt3


class TestParseChoiceSequence:
    """Tests for parse_choice_sequence function."""

    def test_single_digit(self):
        """Test parsing a single digit."""
        result = parse_choice_sequence("3")
        assert result == ["3"]

    def test_concatenated_digits(self):
        """Test parsing concatenated digits like '345'."""
        result = parse_choice_sequence("345")
        assert result == ["3", "4", "5"]

    def test_comma_separated_digits(self):
        """Test parsing comma-separated digits."""
        result = parse_choice_sequence("3,4,5")
        assert result == ["3", "4", "5"]

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        result = parse_choice_sequence(" 3, 4 , 5 ")
        assert result == ["3", "4", "5"]

    def test_empty_input_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="Empty choice"):
            parse_choice_sequence("")

    def test_whitespace_only_raises(self):
        """Test that whitespace-only input raises ValueError."""
        with pytest.raises(ValueError, match="Empty choice"):
            parse_choice_sequence("   ")

    def test_invalid_characters_raise(self):
        """Test that non-digit characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid choice token"):
            parse_choice_sequence("a,b,c")

    def test_mixed_valid_invalid_raises(self):
        """Test that mixed valid/invalid raises ValueError."""
        with pytest.raises(ValueError, match="Invalid choice token"):
            parse_choice_sequence("1,a,3")

    def test_two_digit_single_choice(self):
        """Test that '12' is parsed as two choices, not one."""
        result = parse_choice_sequence("12")
        assert result == ["1", "2"]

    def test_comma_with_two_digit_numbers(self):
        """Test comma-separated numbers work correctly."""
        # Note: Current implementation treats each part as a single token
        result = parse_choice_sequence("1,2,3")
        assert result == ["1", "2", "3"]

    def test_leading_trailing_commas(self):
        """Test handling of leading/trailing commas."""
        result = parse_choice_sequence(",1,2,")
        assert result == ["1", "2"]


class TestFormatMenu:
    """Tests for format_menu function."""

    def test_basic_menu_format(self):
        """Test basic menu formatting."""
        options = [
            MenuOption(key="1", label="Run tests"),
            MenuOption(key="2", label="Build project"),
        ]

        result = format_menu("Main Menu", options, "code_project")

        assert "Main Menu" in result
        assert "Project: code_project" in result
        assert "1. Run tests" in result
        assert "2. Build project" in result

    def test_menu_line_structure(self):
        """Test the line structure of formatted menu."""
        options = [MenuOption(key="1", label="Test")]

        result = format_menu("Title", options, "project")
        lines = result.split("\n")

        assert lines[0] == "Title"
        assert lines[1] == ""  # Empty line after title
        assert "Project: project" in lines[2]
        assert lines[3] == ""  # Empty line after project

    def test_empty_options(self):
        """Test menu with no options."""
        result = format_menu("Empty Menu", [], "test_project")

        assert "Empty Menu" in result
        assert "Project: test_project" in result

    def test_many_options(self):
        """Test menu with many options."""
        options = [MenuOption(key=str(i), label=f"Option {i}") for i in range(1, 10)]

        result = format_menu("Large Menu", options, "big_project")

        for i in range(1, 10):
            assert f"{i}. Option {i}" in result

    def test_special_characters_in_label(self):
        """Test labels with special characters."""
        options = [
            MenuOption(key="1", label="Run tests (unit & integration)"),
            MenuOption(key="2", label="Build: debug mode"),
        ]

        result = format_menu("Special Menu", options, "project")

        assert "Run tests (unit & integration)" in result
        assert "Build: debug mode" in result

    def test_option_indentation(self):
        """Test that options are properly indented."""
        options = [MenuOption(key="1", label="Test")]

        result = format_menu("Title", options, "project")

        # Options should be indented with 2 spaces
        assert "  1. Test" in result


class TestMenuIntegration:
    """Integration tests combining multiple menu functions."""

    def test_parse_and_validate_choices(self):
        """Test parsing choices and validating against menu options."""
        options = [
            MenuOption(key="1", label="Run tests"),
            MenuOption(key="2", label="Build"),
            MenuOption(key="3", label="Deploy"),
        ]
        valid_keys = {opt.key for opt in options}

        # Parse user input
        choices = parse_choice_sequence("123")

        # All choices should be valid
        assert all(choice in valid_keys for choice in choices)

    def test_full_workflow(self):
        """Test complete menu workflow."""
        # Create menu options
        options = [
            MenuOption(key="1", label="Full pipeline"),
            MenuOption(key="2", label="Tests only"),
            MenuOption(key="3", label="Render PDF"),
            MenuOption(key="4", label="Validate"),
            MenuOption(key="0", label="Exit"),
        ]

        # Format menu
        menu_text = format_menu("Pipeline Menu", options, "code_project")

        # Verify menu contains all options
        for opt in options:
            assert f"{opt.key}. {opt.label}" in menu_text

        # Parse a multi-choice
        choices = parse_choice_sequence("2,3,4")
        assert choices == ["2", "3", "4"]

        # Verify choices are valid
        valid_keys = {opt.key for opt in options}
        assert all(c in valid_keys for c in choices)
