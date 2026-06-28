import numpy as np

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from pandas import Series

from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
import logging

from domain_errors import InvalidFileFormatError, MissingColumnError, EmptyMeasurementsError, AppError


@dataclass
class ParticleSizesData:
    """Aggregated particle size data from one or more sources.

    counts maps each source name (filename or 'input_N') to the number of
    measurements contributed by that source.
    """
    sizes: np.ndarray
    counts: dict[str, int]
    total_count: int


class ParticleDataLoader(ABC):
    """Abstract base class for all particle-size data loaders."""
    @abstractmethod
    def load_data(self) -> ParticleSizesData:
        pass


class ConsoleDataLoader(ParticleDataLoader):
    """Reads particle sizes interactively from stdin, grouped by separator tokens."""
    def __init__(self, separator: str, end_of_input: str):
        self.separator = separator
        self.end_of_input = end_of_input

    def _print_user_instructions(self):
        print("Please enter the sizes of particles (one size per line).")
        print("You can use either '.' or ',' for decimals (e.g. 12.5 or 12,5).")
        print()
        print(f"Use '{self.separator}' to separate measurements from different images/files.")
        print(f"Type '{self.end_of_input}' to finish input.")
        print("=====================================================================")

    def load_data(self) -> ParticleSizesData:
        """Reads lines from stdin until end_of_input; separator lines delimit measurement groups."""
        self._print_user_instructions()

        sizes = list[float]()
        counts = dict[str, int]()

        count = 0       # measurements in the current group
        input_number = 1

        input_line = input().strip()
        while input_line != self.end_of_input:
            if input_line == self.separator:
                # commit the current group and start a new one
                counts[f"input_{input_number}"] = count
                input_number += 1
                count = 0

            else:
                try:
                    size = float(input_line.replace(',', '.'))
                    sizes.append(size)
                    count += 1
                except ValueError:
                    print(f"Invalid input '{input_line}'. Please enter a valid number or '{self.separator}' to separate measurements.")
            input_line = input().strip()

        counts[f"input_{input_number}"] = count  # commit the final group

        return ParticleSizesData(sizes=np.array(sizes), counts=counts, total_count=len(sizes))


class CSVDataLoader:
    """Loads particle sizes from a single CSV file."""
    def __init__(self, input_file: Path, particle_column_name: str):
        self.input_file = input_file
        self.particle_column_name = particle_column_name

    def _load_csv_to_dataframe(self, file_path: Path) -> pd.DataFrame:
        """Loads a local CSV file into a Pandas DataFrame."""
        try:
            return pd.read_csv(file_path, encoding='utf-8')

        except FileNotFoundError:
            logging.error(f"File not found: '{file_path}'.")
            raise

        except EmptyDataError:
            logging.error(f"File is empty: '{file_path}'.")
            raise EmptyMeasurementsError()

        except ParserError as ex:
            logging.error(f"Parsing error at '{file_path}': {ex}")
            raise InvalidFileFormatError()

        except PermissionError:
            logging.error(f"Permission denied: '{file_path}'.")
            raise

        except Exception as ex:
            logging.error(f"Unexpected error loading CSV '{file_path}': {ex}")
            raise


    def load_data(self) -> np.ndarray | None:
        """
        Loads particle sizes from a CSV file and returns them as a NumPy array. 
        Returns None if no valid measurements are found.
        """
        try:
            df : pd.DataFrame = self._load_csv_to_dataframe(self.input_file)
            series: Series = df[self.particle_column_name].dropna()
            try:
            # replacing , with . and explicitly requiring numeric type
                sizes :np.ndarray = series.astype(str).str.replace(',', '.').astype(np.float64).to_numpy()
            except ValueError as ex:
                raise InvalidFileFormatError() from ex  # column contains non-numeric values
            
            
            if len(sizes) == 0:
                raise EmptyMeasurementsError()
            
            return sizes
        
        except EmptyMeasurementsError as e:
            logging.warning(e.message + f" Skipping file '{self.input_file}'.")
            return None
        
        except KeyError as ex:
            error: MissingColumnError = MissingColumnError(self.particle_column_name)
            logging.error(error.message)
            raise error from ex
        
        except (FileNotFoundError, InvalidFileFormatError, PermissionError) as e:
            raise  # propagate raw so DirectoryCSVDataLoader can track them as invalid files
        
        except Exception as ex:  # last-resort catch to ensure the error is logged
            logging.error(f"An unexpected error occurred while loading data from '{self.input_file}': {ex}")
            raise


class DirectoryCSVDataLoader(ParticleDataLoader):
    """Recursively loads particle sizes from all CSV files in a directory."""
    def __init__(self, directory_path: Path, particle_column_name: str):
        self.directory_path : Path = directory_path
        self.csv_paths :list[Path] = list(self.directory_path.rglob("*.csv"))
        self.particle_column_name : str = particle_column_name

    def load_data(self) -> ParticleSizesData:
        """Aggregates sizes from every CSV; raises AppError if any file could not be loaded."""
        sizes = list[float]()
        counts = dict[str, int]()
        invalid_files = []

        for csv_filepath in self.csv_paths:
            csv_loader = CSVDataLoader(csv_filepath, self.particle_column_name)
            try:
                particle_sizes = csv_loader.load_data()
                if particle_sizes is not None:
                    # flatten guards against unexpected 2-D arrays from multi-column CSVs
                    sizes.extend(particle_sizes.flatten())
                    counts[csv_filepath.name] = len(particle_sizes)

            except (FileNotFoundError, InvalidFileFormatError, MissingColumnError, PermissionError) as e:
                invalid_files.append(csv_filepath.name)
                continue  # Skip to the next file

        # raise rather than silently return partial data — the user must fix broken files
        if (invalid_count := len(invalid_files)) > 0:
            message = (
                f"{invalid_count} file(s) could not be loaded and were skipped: "
                f"{', '.join(invalid_files)}. Please fix these files and rerun the application."
            )
            logging.warning(message)
            raise AppError(message)

        elif (len(sizes) == 0):
            message = "No valid particle size measurements were found in the provided CSV files."
            logging.error(message)
            raise EmptyMeasurementsError()

        return ParticleSizesData(sizes=np.array(sizes), counts=counts, total_count=len(sizes))
        

    