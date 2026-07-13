class VexError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(message)

    def __str__(self):
        if self.line is not None:
            return f"Error on line {self.line}: {self.message}"
        return self.message
