"""Custom exceptions for the Active Inference Meta-Pragmatic Framework."""


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