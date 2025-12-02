"""Expression Parser and Generator for Boundary Logic.

This module provides tools for:
- Parsing boundary form expressions from string notation
- Generating boundary forms programmatically
- Converting between different representations
- Creating test expressions for verification

Notation Conventions:
    - ⟨ ⟩ or () or [] : mark/cross (enclosure)
    - Juxtaposition : AND (spatial adjacency)
    - Empty/void : FALSE
    - Nested brackets : composition
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from src.forms import Form, make_void, make_mark, enclose, juxtapose


class TokenType(Enum):
    """Token types for parsing."""
    OPEN = "open"       # Opening bracket
    CLOSE = "close"     # Closing bracket
    VOID = "void"       # Void marker
    EOF = "eof"         # End of input


@dataclass
class Token:
    """A token from lexical analysis."""
    type: TokenType
    value: str
    position: int


class ExpressionParser:
    """Parser for boundary form expressions.
    
    Supports multiple bracket styles:
    - Angle brackets: ⟨ ⟩
    - Parentheses: ( )
    - Square brackets: [ ]
    - Curly braces: { }
    """
    
    OPEN_BRACKETS = "⟨([{"
    CLOSE_BRACKETS = "⟩)]}"
    
    def __init__(self, text: str) -> None:
        """Initialize parser with input text.
        
        Args:
            text: Expression string to parse
        """
        self.text = text.strip()
        self.pos = 0
        self.length = len(self.text)
    
    def parse(self) -> Form:
        """Parse the expression into a Form.
        
        Returns:
            Parsed Form object
        """
        if not self.text:
            return make_void()
        
        forms = self._parse_sequence()
        
        if len(forms) == 0:
            return make_void()
        elif len(forms) == 1:
            return forms[0]
        else:
            return Form(contents=forms, is_marked=False)
    
    def _parse_sequence(self) -> List[Form]:
        """Parse a sequence of juxtaposed forms.
        
        Returns:
            List of parsed forms
        """
        forms = []
        
        while self.pos < self.length:
            self._skip_whitespace()
            
            if self.pos >= self.length:
                break
            
            char = self.text[self.pos]
            
            if char in self.OPEN_BRACKETS:
                form = self._parse_enclosed()
                forms.append(form)
            elif char in self.CLOSE_BRACKETS:
                # End of current enclosure
                break
            else:
                # Skip other characters (potential variable markers)
                self.pos += 1
        
        return forms
    
    def _parse_enclosed(self) -> Form:
        """Parse an enclosed form (within brackets).
        
        Returns:
            Enclosed Form
        """
        open_char = self.text[self.pos]
        expected_close = self.CLOSE_BRACKETS[self.OPEN_BRACKETS.index(open_char)]
        
        self.pos += 1  # Skip opening bracket
        
        # Parse contents
        contents = self._parse_sequence()
        
        # Expect closing bracket
        if self.pos < self.length and self.text[self.pos] == expected_close:
            self.pos += 1
        
        return Form(contents=contents, is_marked=True)
    
    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < self.length and self.text[self.pos] in " \t\n\r":
            self.pos += 1


def parse_expression(text: str) -> Form:
    """Parse a boundary form expression from string.
    
    Args:
        text: Expression string
        
    Returns:
        Parsed Form
        
    Examples:
        >>> parse_expression("⟨⟩")  # Simple mark
        >>> parse_expression("⟨⟨⟩⟩")  # Double enclosure
        >>> parse_expression("⟨⟩⟨⟩")  # Two juxtaposed marks
        >>> parse_expression("")  # Void
    """
    parser = ExpressionParser(text)
    return parser.parse()


def parse(text: str) -> Form:
    """Alias for parse_expression."""
    return parse_expression(text)


class ExpressionGenerator:
    """Generator for random and structured boundary forms.
    
    Useful for:
    - Testing reduction algorithms
    - Generating examples
    - Creating benchmark expressions
    """
    
    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
    
    def random_form(self, max_depth: int = 3, max_width: int = 3) -> Form:
        """Generate a random boundary form.
        
        Args:
            max_depth: Maximum nesting depth
            max_width: Maximum children at each level
            
        Returns:
            Random Form
        """
        return self._generate(max_depth, max_width)
    
    def _generate(self, depth: int, width: int) -> Form:
        """Recursive form generation.
        
        Args:
            depth: Remaining depth allowed
            width: Maximum children
            
        Returns:
            Generated Form
        """
        if depth <= 0:
            # Base case: void or simple mark
            return make_mark() if random.random() > 0.5 else make_void()
        
        # Decide structure
        choice = random.random()
        
        if choice < 0.2:
            # Void
            return make_void()
        elif choice < 0.4:
            # Simple mark
            return make_mark()
        elif choice < 0.7:
            # Enclosed form
            num_children = random.randint(0, width)
            children = [self._generate(depth - 1, width) for _ in range(num_children)]
            return Form(contents=children, is_marked=True)
        else:
            # Juxtaposed forms
            num_children = random.randint(2, width)
            children = [self._generate(depth - 1, width) for _ in range(num_children)]
            return Form(contents=children, is_marked=False)
    
    def generate_reducible(self, target_steps: int = 3) -> Form:
        """Generate a form that requires multiple reduction steps.
        
        Creates forms with deliberate calling and crossing patterns.
        
        Args:
            target_steps: Approximate number of reduction steps
            
        Returns:
            Reducible Form
        """
        form = make_mark()
        
        for _ in range(target_steps):
            operation = random.choice(["double_enclose", "duplicate_mark"])
            
            if operation == "double_enclose":
                # Add double enclosure (calling pattern)
                form = Form.enclose(Form.enclose(form))
            else:
                # Add duplicate mark (crossing pattern)
                form = Form(
                    contents=[form, make_mark()],
                    is_marked=form.is_marked
                )
        
        return form
    
    def generate_canonical(self) -> Form:
        """Generate a form already in canonical form.
        
        Returns:
            Canonical Form (void or simple mark)
        """
        return make_mark() if random.random() > 0.5 else make_void()


def generate_random_form(max_depth: int = 3, max_width: int = 3, seed: int = None) -> Form:
    """Generate a random boundary form.
    
    Args:
        max_depth: Maximum nesting depth
        max_width: Maximum children per level
        seed: Random seed
        
    Returns:
        Random Form
    """
    gen = ExpressionGenerator(seed)
    return gen.random_form(max_depth, max_width)


def generate_test_suite() -> List[Tuple[str, Form]]:
    """Generate a suite of test forms covering various patterns.
    
    Returns:
        List of (name, form) tuples
    """
    return [
        # Basic forms
        ("void", make_void()),
        ("mark", make_mark()),
        
        # Calling pattern (should reduce)
        ("double_mark", parse("⟨⟨⟩⟩")),
        ("triple_mark", parse("⟨⟨⟨⟩⟩⟩")),
        
        # Crossing pattern (should reduce)
        ("two_marks", parse("⟨⟩⟨⟩")),
        ("three_marks", Form.juxtapose(make_mark(), make_mark(), make_mark())),
        
        # Mixed patterns
        ("enclosed_double", parse("⟨⟨⟩⟨⟩⟩")),
        ("nested_mixed", parse("⟨⟨⟨⟩⟩⟨⟩⟩")),
        
        # Already canonical
        ("simple_enclosed", parse("⟨⟩")),
        ("empty", parse("")),
    ]


def format_form(form: Form, style: str = "unicode") -> str:
    """Format a form for display.
    
    Args:
        form: Form to format
        style: Display style ("unicode", "ascii", "latex")
        
    Returns:
        Formatted string
    """
    if style == "unicode":
        return form.to_string("angle")
    elif style == "ascii":
        return form.to_string("paren")
    elif style == "latex":
        return _form_to_latex(form)
    else:
        return str(form)


def _form_to_latex(form: Form) -> str:
    """Convert form to LaTeX notation.
    
    Args:
        form: Form to convert
        
    Returns:
        LaTeX string
    """
    if form.is_void():
        return r"\emptyset"
    
    inner = "".join(_form_to_latex(f) for f in form.contents)
    
    if form.is_marked:
        return r"\langle " + inner + r" \rangle"
    else:
        return inner


def forms_from_boolean_table(n_vars: int = 2) -> Dict[str, Form]:
    """Generate forms for all Boolean functions of n variables.
    
    Args:
        n_vars: Number of variables (default 2)
        
    Returns:
        Dictionary mapping function names to forms
    """
    from src.algebra import BooleanAlgebra
    
    ba = BooleanAlgebra
    
    if n_vars == 2:
        a = make_mark()  # Variable A represented as mark
        b = make_void()  # Variable B represented as void (for distinct testing)
        
        return {
            "false": ba.false_(),
            "true": ba.true_(),
            "not_a": ba.not_(a),
            "not_b": ba.not_(b),
            "a_and_b": ba.and_(a, b),
            "a_or_b": ba.or_(a, b),
            "a_nand_b": ba.nand(a, b),
            "a_nor_b": ba.nor(a, b),
            "a_xor_b": ba.xor(a, b),
            "a_implies_b": ba.implies(a, b),
            "a_iff_b": ba.iff(a, b),
        }
    
    return {"true": ba.true_(), "false": ba.false_()}

