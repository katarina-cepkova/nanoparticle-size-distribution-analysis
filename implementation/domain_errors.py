


class AppError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message: str = "An unexpected error occurred."):
        self.message :str = message
        super().__init__(message)


class InvalidInputError(AppError):
    """Raised when the input data is invalid or cannot be processed."""
    def __init__(self, message: str = "The input data is invalid."):
        super().__init__(message)


class InvalidFileFormatError(AppError):
    """Raised when a file's format/structure doesn't match what's expected."""
    def __init__(self):
        super().__init__("The input file format is invalid.")


class MissingColumnError(InvalidInputError):
    """Raised when an expected column is not found in the input file."""
    def __init__(self, column: str):
        super().__init__(f"The input file is missing a column '{column}'.")


class EmptyMeasurementsError(InvalidInputError):
    """Raised when the input contains no valid measurements."""
    def __init__(self):
        super().__init__("The input data contains no valid measurements.")