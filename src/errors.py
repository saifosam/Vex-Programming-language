"""User-facing error types for Vex parse and runtime errors."""

from __future__ import annotations


class VexError(Exception):
    """Raised when something is wrong in a user's .vex file.

    Attributes:
        message: Human-readable error description.
        line: Optional source line number where the error occurred.
    """

    def __init__(self, message: str, line: int | None = None) -> None:
        self.message = message
        self.line = line
        super().__init__(message)

    def display(self) -> str:
        """Return a user-friendly, line-annotated error string."""
        if self.line is not None:
            return f"Error on line {self.line}: {self.message}"
        return f"Error: {self.message}"
