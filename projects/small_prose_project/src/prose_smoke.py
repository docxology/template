"""Minimal source module for prose project.

Provides a simple utility function to satisfy pipeline requirements.
No domain logic - this is purely for testing and coverage.
"""


def identity(x):
    """Return input unchanged.

    This trivial function exists solely to satisfy the pipeline's
    requirement for source code and test coverage. It performs
    no meaningful computation.

    Args:
        x: Any value

    Returns:
        The input value unchanged

    Examples:
        >>> identity(42)
        42
        >>> identity("hello")
        'hello'
    """
    return x


def constant_value():
    """Return a constant value for testing.

    Returns:
        int: Always returns 42
    """
    return 42