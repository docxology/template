"""Custom exceptions for the Ento-Linguistic Research Project."""

__all__ = [
    "ValidationError",
    "EntoLinguisticsError",
]


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, context: dict = None, suggestions: list = None):
        """Initialize validation error.

        Args:
            message: Error message
            context: Additional context information
            suggestions: Suggested actions to fix the error
        """
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []

        super().__init__(message)

class EntoLinguisticsError(Exception):
    """Base class for Ento-Linguistic exceptions."""
    pass
