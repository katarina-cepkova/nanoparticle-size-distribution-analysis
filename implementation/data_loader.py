import numpy as np

from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
import logging

from domain_errors import InvalidFileFormatError, MissingColumnError, EmptyMeasurementsError, AppError, UnsupportedFileTypeError
from file_loader import FileLoader, CsvFileLoader, ExcelFileLoader


@dataclass
class ParticleSizesData:
    """Aggregated particle size data from one or more sources.

    `counts` maps each source name (filename or 'input_N') to the number of
    measurements contributed by that source.
    """
    sizes :np.ndarray
    counts :dict[str, int]
    total_count :int


class DataLoader(ABC):
    """Abstract base class for all particle-size data loaders."""

    @abstractmethod
    def load_data(self) -> ParticleSizesData:
        pass


class ConsoleLoader(DataLoader):
    """Reads particle sizes interactively from stdin, grouped by separator tokens."""

    def __init__(self, separator: str, end_of_input: str) -> None:
        self.separator :str = separator
        self.end_of_input :str = end_of_input


    def _print_user_instructions(self) -> None:
        print("Please enter the sizes of particles (one size per line).")
        print("You can use either '.' or ',' for decimals (e.g. 12.5 or 12,5).")
        print()
        print(f"Use '{self.separator}' to separate measurements from different images/files.")
        print(f"Type '{self.end_of_input}' to finish input.")
        print("=====================================================================")


    def load_data(self) -> ParticleSizesData:
        """Reads lines from stdin until end_of_input; separator lines delimit measurement groups."""
        self._print_user_instructions()

        sizes :list[float] = []
        counts :dict[str, int] = {}

        count :int = 0       # measurements in the current group
        input_number :int = 1

        input_line :str = input().strip()
        while input_line != self.end_of_input:
            if input_line == self.separator:
                # commit the current group and start a new one
                counts[f"input_{input_number}"] = count
                input_number += 1
                count = 0

            else:
                try:
                    size :float = float(input_line.replace(',', '.'))
                    sizes.append(size)
                    count += 1
                except ValueError:
                    print(f"Invalid input '{input_line}'. Please enter a valid number or '{self.separator}' to separate measurements.")
            input_line = input().strip()

        counts[f"input_{input_number}"] = count  # commit the final group
        if (len(sizes) == 0):
            err :EmptyMeasurementsError = EmptyMeasurementsError(Path("console input"))
            logging.error(err.message)
            raise err

        return ParticleSizesData(sizes=np.array(sizes), counts=counts, total_count=len(sizes))


class DirectoryLoader(DataLoader):
    """Abstract base class for data loaders that recursively read from a directory."""


    def __init__(self, directory_path: Path, particle_column_name: str = "Length", particle_column_index: int = -1) -> None:
        self.directory_path :Path = directory_path
        self.particle_column_name :str = particle_column_name
        self.particle_column_index :int = particle_column_index
        self.file_paths :list[Path]= []

        for p in self.directory_path.rglob("*"):
            if p.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                self.file_paths.append(p)


    def _create_loader(self, file_path: Path) -> FileLoader:
        """Factory method to create the appropriate loader based on file extension."""
        if file_path.suffix.lower() == '.csv':
            return CsvFileLoader(file_path, self.particle_column_name)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            return ExcelFileLoader(file_path, self.particle_column_index)
        else:
            er :UnsupportedFileTypeError = UnsupportedFileTypeError(file_path)
            logging.error(er.message)
            raise er


    def load_data(self) -> ParticleSizesData:
        sizes :list[float] = []
        counts :dict[str, int] = {}
        invalid_files :list[str] = []

        for path in self.file_paths:
            file_loader :FileLoader = self._create_loader(path)
            try:
                particle_sizes :np.ndarray | None = file_loader.load_data()
                if particle_sizes is not None:
                    # flatten guards against unexpected 2-D arrays from multi-column CSVs
                    sizes.extend(particle_sizes.flatten())
                    counts[path.name] = len(particle_sizes)

            except Exception as e: # FileNotFoundError, InvalidFileFormatError, MissingColumnError, UnsupportedFileTypeError, PermissionError...
                invalid_files.append(path.name)
                logging.error(f"Skipping '{path.name}': {e}")
                continue  # Skip to the next file

        # raise rather than silently return partial data — the user must fix broken files
        if (invalid_count := len(invalid_files)) > 0:
            message :str = (
                f"{invalid_count} file(s) could not be loaded and were skipped: "
                f"{', '.join(invalid_files)}. Please fix these files and rerun the application."
            )
            logging.warning(message)
            raise AppError(message)

        elif (len(sizes) == 0):
            message :str = "No valid particle size measurements were found in the provided files."
            logging.error(message)
            raise EmptyMeasurementsError(self.directory_path)

        return ParticleSizesData(sizes=np.array(sizes), counts=counts, total_count=len(sizes))