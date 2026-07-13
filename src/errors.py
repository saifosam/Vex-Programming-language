class VexError(Exception):
    """Raised when something is wrong in a user's .vex file."""
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(message)

    def display(self):
        if self.line is not None:
            return f"Error on line {self.line}: {self.message}"
        return f"Error: {self.message}"