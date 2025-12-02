"""Boundary Logic Forms - Core module for Containment Theory.

This module implements the fundamental structures of G. Spencer-Brown's
Laws of Form (1969), providing a computational foundation for boundary logic
as an alternative to traditional set-theoretic foundations.

The primary distinction (mark) creates inside/outside relationships,
replacing set membership with spatial containment.

Key Concepts:
    - Form: A recursive structure of nested boundaries
    - Mark: The primary distinction ⟨ ⟩ creating inside/outside
    - Void: Empty space, the absence of distinction (FALSE in Boolean)
    - Cross: The marked state ⟨ ⟩ (TRUE in Boolean)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator, List, Optional, Tuple, Union


class FormType(Enum):
    """Types of forms in boundary logic."""
    VOID = "void"       # Empty space (FALSE)
    MARK = "mark"       # Marked cross ⟨ ⟩ (TRUE)
    FORM = "form"       # Nested structure


@dataclass
class Form:
    """A boundary form in the calculus of indications.
    
    A Form represents a structure in Spencer-Brown's boundary logic.
    Forms can be:
    - Void (empty): Represents FALSE / unmarked state
    - Mark (cross): Represents TRUE / marked state ⟨ ⟩
    - Nested: Contains other forms within boundaries
    
    The two fundamental axioms:
    1. Calling (Involution): ⟨⟨a⟩⟩ = a (double crossing returns)
    2. Crossing: ⟨ ⟩⟨ ⟩ = ⟨ ⟩ (condensation of marks)
    
    Attributes:
        contents: List of forms contained within this boundary
        is_marked: Whether this form has a boundary (is enclosed)
    """
    contents: List[Form] = field(default_factory=list)
    is_marked: bool = False
    
    def __post_init__(self) -> None:
        """Validate form structure after initialization."""
        if self.contents is None:
            self.contents = []
    
    @classmethod
    def void(cls) -> Form:
        """Create an empty void form (FALSE).
        
        Returns:
            Form representing void/empty space
        """
        return cls(contents=[], is_marked=False)
    
    @classmethod
    def mark(cls) -> Form:
        """Create a simple mark/cross form (TRUE).
        
        The mark ⟨ ⟩ is the primary distinction, representing TRUE
        in Boolean logic.
        
        Returns:
            Form representing the marked state
        """
        return cls(contents=[], is_marked=True)
    
    @classmethod
    def cross(cls) -> Form:
        """Alias for mark() - creates the crossing."""
        return cls.mark()
    
    @classmethod
    def enclose(cls, *forms: Form) -> Form:
        """Create a form enclosing other forms within a boundary.
        
        In notation: ⟨a b c⟩ encloses forms a, b, c.
        
        Args:
            *forms: Forms to enclose within a boundary
            
        Returns:
            New form with the given forms enclosed
        """
        return cls(contents=list(forms), is_marked=True)
    
    @classmethod
    def juxtapose(cls, *forms: Form) -> Form:
        """Create a form by placing forms side by side (no boundary).
        
        Juxtaposition represents AND in Boolean logic.
        
        Args:
            *forms: Forms to place side by side
            
        Returns:
            New unmarked form containing juxtaposed forms
        """
        return cls(contents=list(forms), is_marked=False)
    
    @classmethod
    def from_string(cls, s: str) -> Form:
        """Parse a form from string notation.
        
        Notation:
        - ⟨⟩ or () or [] represents a mark
        - ⟨a⟩ or (a) represents enclosure
        - ab represents juxtaposition
        - Empty string represents void
        
        Args:
            s: String representation of form
            
        Returns:
            Parsed Form object
        """
        s = s.strip()
        if not s:
            return cls.void()
        return _parse_form(s)
    
    def is_void(self) -> bool:
        """Check if this form is void (empty, unmarked).
        
        Returns:
            True if form is void (no contents, no mark)
        """
        return not self.is_marked and len(self.contents) == 0
    
    def is_simple_mark(self) -> bool:
        """Check if this is a simple mark ⟨ ⟩ with no contents.
        
        Returns:
            True if form is ⟨ ⟩ exactly
        """
        return self.is_marked and len(self.contents) == 0
    
    def depth(self) -> int:
        """Calculate the nesting depth of the form.
        
        Returns:
            Maximum nesting depth (0 for void, 1 for simple mark)
        """
        if not self.contents:
            return 1 if self.is_marked else 0
        max_child_depth = max(f.depth() for f in self.contents)
        return max_child_depth + (1 if self.is_marked else 0)
    
    def size(self) -> int:
        """Calculate the total number of marks in the form.
        
        Returns:
            Count of all marks (boundaries) in the form
        """
        count = 1 if self.is_marked else 0
        for f in self.contents:
            count += f.size()
        return count
    
    def to_string(self, style: str = "angle") -> str:
        """Convert form to string notation.
        
        Args:
            style: Bracket style - "angle" for ⟨⟩, "paren" for (), "square" for []
            
        Returns:
            String representation of the form
        """
        brackets = {
            "angle": ("⟨", "⟩"),
            "paren": ("(", ")"),
            "square": ("[", "]"),
        }
        left, right = brackets.get(style, ("⟨", "⟩"))
        
        if self.is_void():
            return ""
        
        inner = "".join(f.to_string(style) for f in self.contents)
        
        if self.is_marked:
            return f"{left}{inner}{right}"
        else:
            return inner
    
    def __str__(self) -> str:
        """String representation using angle brackets."""
        return self.to_string("angle") or "∅"  # ∅ for void
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"Form({self.to_string('paren') or 'void'})"
    
    def __eq__(self, other: object) -> bool:
        """Check structural equality of forms."""
        if not isinstance(other, Form):
            return False
        return self.is_marked == other.is_marked and self.contents == other.contents
    
    def __hash__(self) -> int:
        """Hash based on structure."""
        return hash((self.is_marked, tuple(self.contents)))
    
    def copy(self) -> Form:
        """Create a deep copy of the form.
        
        Returns:
            New Form with copied structure
        """
        return Form(
            contents=[f.copy() for f in self.contents],
            is_marked=self.is_marked
        )
    
    def iter_subforms(self) -> Iterator[Form]:
        """Iterate over all subforms including self.
        
        Yields:
            Each form in the structure (depth-first)
        """
        yield self
        for f in self.contents:
            yield from f.iter_subforms()
    
    def flatten_contents(self) -> List[Form]:
        """Get all direct contents as a flat list.
        
        Returns:
            List of immediate child forms
        """
        return list(self.contents)


def make_void() -> Form:
    """Create a void form (empty, unmarked).
    
    Void represents FALSE in Boolean logic and is the
    absence of any distinction.
    
    Returns:
        Void Form
    """
    return Form.void()


def make_mark() -> Form:
    """Create a simple mark ⟨ ⟩.
    
    The mark is the primary distinction, representing TRUE
    in Boolean logic.
    
    Returns:
        Mark Form ⟨ ⟩
    """
    return Form.mark()


def make_cross() -> Form:
    """Alias for make_mark - the cross is the marked state."""
    return make_mark()


def enclose(*forms: Form) -> Form:
    """Enclose forms within a boundary.
    
    Creates ⟨forms⟩ - equivalent to NOT(AND(forms)) in Boolean.
    
    Args:
        *forms: Forms to enclose
        
    Returns:
        Enclosed Form
    """
    return Form.enclose(*forms)


def juxtapose(*forms: Form) -> Form:
    """Place forms side by side without boundary.
    
    Juxtaposition represents AND in Boolean logic.
    
    Args:
        *forms: Forms to juxtapose
        
    Returns:
        Juxtaposed Form
    """
    return Form.juxtapose(*forms)


def negate(form: Form) -> Form:
    """Create the negation of a form by enclosing it.
    
    In boundary logic, negation is simply enclosure:
    ⟨a⟩ = NOT a
    
    Args:
        form: Form to negate
        
    Returns:
        Negated Form
    """
    return Form.enclose(form)


def conjunction(*forms: Form) -> Form:
    """Create the conjunction (AND) of forms.
    
    Conjunction is juxtaposition in boundary logic.
    
    Args:
        *forms: Forms to AND together
        
    Returns:
        Conjunction Form
    """
    return Form.juxtapose(*forms)


def disjunction(*forms: Form) -> Form:
    """Create the disjunction (OR) of forms.
    
    OR(a, b) = ⟨⟨a⟩⟨b⟩⟩ in boundary logic (De Morgan via enclosure).
    
    Args:
        *forms: Forms to OR together
        
    Returns:
        Disjunction Form
    """
    negated = [Form.enclose(f) for f in forms]
    return Form.enclose(Form.juxtapose(*negated))


def implication(antecedent: Form, consequent: Form) -> Form:
    """Create implication: antecedent → consequent.
    
    a → b = ⟨a⟩ OR b = ⟨⟨⟨a⟩⟩⟨b⟩⟩ (simplified: ⟨a⟨b⟩⟩)
    
    Actually: a → b = NOT a OR b = ⟨a⟩ OR b
    In boundary: ⟨⟨⟨a⟩⟩⟨b⟩⟩ = ⟨a⟨b⟩⟩
    
    Args:
        antecedent: The 'if' part
        consequent: The 'then' part
        
    Returns:
        Implication Form
    """
    return Form.enclose(antecedent, Form.enclose(consequent))


def equivalence(form1: Form, form2: Form) -> Form:
    """Create logical equivalence: form1 ↔ form2.
    
    a ↔ b = (a → b) AND (b → a)
    
    Args:
        form1: First form
        form2: Second form
        
    Returns:
        Equivalence Form
    """
    return conjunction(
        implication(form1, form2),
        implication(form2, form1)
    )


def _parse_form(s: str) -> Form:
    """Parse form from string (internal recursive parser).
    
    Handles nested brackets and juxtaposition.
    
    Args:
        s: String to parse
        
    Returns:
        Parsed Form
    """
    s = s.strip()
    
    if not s:
        return Form.void()
    
    # Map bracket types
    open_brackets = "⟨([{"
    close_brackets = "⟩)]}"
    
    # Check if entire string is enclosed
    if len(s) >= 2 and s[0] in open_brackets:
        open_char = s[0]
        close_char = close_brackets[open_brackets.index(open_char)]
        
        # Find matching close bracket
        depth = 1
        for i in range(1, len(s)):
            if s[i] in open_brackets:
                depth += 1
            elif s[i] in close_brackets:
                depth -= 1
                if depth == 0:
                    if i == len(s) - 1:
                        # Entire string is enclosed
                        inner = s[1:-1]
                        contents = _parse_juxtaposition(inner)
                        return Form(contents=contents, is_marked=True)
                    break
    
    # Parse as juxtaposition
    contents = _parse_juxtaposition(s)
    if len(contents) == 1:
        return contents[0]
    return Form(contents=contents, is_marked=False)


def _parse_juxtaposition(s: str) -> List[Form]:
    """Parse juxtaposed forms from string.
    
    Args:
        s: String containing juxtaposed forms
        
    Returns:
        List of parsed forms
    """
    if not s.strip():
        return []
    
    forms = []
    open_brackets = "⟨([{"
    close_brackets = "⟩)]}"
    
    i = 0
    while i < len(s):
        if s[i] in " \t\n":
            i += 1
            continue
        
        if s[i] in open_brackets:
            # Find matching close
            open_char = s[i]
            close_char = close_brackets[open_brackets.index(open_char)]
            depth = 1
            start = i
            i += 1
            while i < len(s) and depth > 0:
                if s[i] in open_brackets:
                    depth += 1
                elif s[i] in close_brackets:
                    depth -= 1
                i += 1
            forms.append(_parse_form(s[start:i]))
        else:
            # Single character as variable (for parsing expressions)
            if s[i].isalnum():
                # For now, treat alphanumeric as void (placeholder)
                i += 1
            else:
                i += 1
    
    return forms


def forms_equal(f1: Form, f2: Form) -> bool:
    """Check if two forms are structurally equal.
    
    Args:
        f1: First form
        f2: Second form
        
    Returns:
        True if forms are structurally identical
    """
    return f1 == f2


def is_canonical(form: Form) -> bool:
    """Check if a form is in canonical (reduced) form.
    
    A canonical form cannot be further simplified using
    the axioms of calling and crossing.
    
    Args:
        form: Form to check
        
    Returns:
        True if form is in canonical form
    """
    # Void is canonical
    if form.is_void():
        return True
    
    # Simple mark is canonical
    if form.is_simple_mark():
        return True
    
    # Check for double enclosure (violates calling axiom)
    if form.is_marked and len(form.contents) == 1:
        inner = form.contents[0]
        if inner.is_marked and len(inner.contents) == 1:
            return False  # ⟨⟨a⟩⟩ can be reduced
    
    # Check for adjacent marks (violates crossing axiom)
    mark_count = sum(1 for f in form.contents if f.is_simple_mark())
    if mark_count > 1:
        return False  # ⟨ ⟩⟨ ⟩ can be reduced
    
    # Recursively check contents
    for f in form.contents:
        if not is_canonical(f):
            return False
    
    return True

