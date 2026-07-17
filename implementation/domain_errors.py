from pathlib import Path


class AppError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message: str = "An unexpected error occurred.") -> None:
        self.message :str = message
        super().__init__(message)


class InvalidInputError(AppError):
    """Raised when the input data is invalid or cannot be processed."""

    def __init__(self, message: str = "The input data is invalid.") -> None:
        super().__init__(message)


class InvalidFileFormatError(AppError):
    """Raised when a file's format/structure doesn't match what's expected."""

    def __init__(self, file_path: Path) -> None:
        super().__init__(f"The input file '{file_path.name}' has an invalid format.")


class MissingColumnError(InvalidInputError):
    """Raised when an expected column is not found in the input file."""

    def __init__(self, column: str, file_path: Path) -> None:
        super().__init__(f"Missing column '{column}' in '{file_path.name}'.")


class EmptyMeasurementsError(InvalidInputError):
    """Raised when the input contains no valid measurements."""

    def __init__(self, file_path: Path) -> None:
        super().__init__(f"No valid measurements found in '{file_path.name}'.")


class UnsupportedFileTypeError(AppError):
    """Raised when the input file type is not supported."""

    def __init__(self, file_path: Path) -> None:
        super().__init__(f"The input file '{file_path.name}' has an unsupported file type.")


class OutputPathError(AppError):
    """Raised when a configured output path can't be opened for writing."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"Cannot write to '{path}': {reason}")