from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO


class Printer(ABC):
    """
    Abstract output target for the printed report. All print_* functions below
    take a Printer instead of calling the builtin print() directly, so the
    exact same report can be written either to the console or to a .txt file
    (or anywhere else a future Printer implementation sends it) just by
    swapping which Printer instance gets passed in.
    """

    @abstractmethod
    def print(self, text: str = "") -> None:
        """Writes one line of text (with a trailing newline) to the output target."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Releases any resources held by the output target. Called once the report is done."""
        ...


class ConsolePrinter(Printer):
    """Writes report output to standard output (the console)."""

    def print(self, text: str = "") -> None:
        """Writes one line of text (with a trailing newline) to stdout."""
        print(text)

    def close(self) -> None:
        """No-op: stdout has no resource to release."""
        pass


class FilePrinter(Printer):
    """
    Writes report output to a text file, one line per print() call.
    Opens the file immediately (truncating any existing content) and keeps it
    open until close() is called — remember to call close() when the report
    is finished, e.g. via a try/finally in the caller.
    """

    def __init__(self, path: Path) -> None:
        self.path :Path = path
        self._file :TextIO = open(path, "w", encoding="utf-8")


    def print(self, text: str = "") -> None:
        """Writes one line of text (with a trailing newline) to the file."""
        self._file.write(text + "\n")


    def close(self) -> None:
        """Closes the underlying file handle. Must be called once the report is done."""
        self._file.close()


class CompositePrinter(Printer):
    """Fans out report output to a group of Printers, e.g. console and file at once."""

    def __init__(self, printers :list[Printer]) -> None:
        """Stores the Printers to fan out to."""
        self.printers :list[Printer] = printers

    def print(self, text: str = "") -> None:
        """Writes one line of text to every wrapped Printer."""
        for printer in self.printers:
            printer.print(text)

    def close(self) -> None:
        """Closes every wrapped Printer."""
        for printer in self.printers:
            printer.close()
