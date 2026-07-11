import numpy as np

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from pandas import Series

import zipfile
import xml.etree.ElementTree as ET
from openpyxl.utils.exceptions import InvalidFileException

from abc import ABC, abstractmethod
from pathlib import Path
import logging

from domain_errors import InvalidFileFormatError, MissingColumnError, EmptyMeasurementsError


def derive_dataset_label(input_data_path: Path) -> str | None:
    """Returns the subfolder name if input_data contains exactly one child, and it's a folder."""
    children = [p for p in input_data_path.iterdir() if not p.name.startswith(".")]

    if len(children) == 1 and children[0].is_dir():
        return children[0].name

    return None


class FileLoader(ABC):
    """Abstract base class for data loaders that read from a single file."""

    @abstractmethod
    def load_data(self) -> np.ndarray | None:
        pass


class CsvFileLoader(FileLoader):
    """Loads particle sizes from a single CSV file."""

    def __init__(self, input_file: Path, particle_column_name: str) -> None:
        self.input_file :Path = input_file
        self.particle_column_name :str = particle_column_name


    def _load_csv_to_dataframe(self) -> pd.DataFrame:
        """Loads a local CSV file into a Pandas DataFrame."""
        try:
            return pd.read_csv(self.input_file, encoding='utf-8')

        except FileNotFoundError:
            logging.error(f"File not found: '{self.input_file}'.")
            raise

        except EmptyDataError:
            logging.error(f"File is empty: '{self.input_file}'.")
            raise EmptyMeasurementsError(self.input_file)

        except ParserError as e:
            logging.error(f"Parsing error at '{self.input_file}': {e}")
            raise InvalidFileFormatError(self.input_file)

        except PermissionError:
            logging.error(f"Permission denied: '{self.input_file}'.")
            raise

        except OSError as e:
            logging.error(f"System-level I/O error while reading a CSV file occurred: {e}")
            raise


    def load_data(self) -> np.ndarray | None:
        """
        Loads particle sizes from a CSV file and returns them as a NumPy array. 
        Returns None if no valid measurements are found.
        """
        try:
            df :pd.DataFrame = self._load_csv_to_dataframe()
            series :Series = df[self.particle_column_name].dropna()
            try:
            # replacing , with . and explicitly requiring numeric type
                sizes :np.ndarray = series.astype(str).str.replace(',', '.').astype(np.float64).to_numpy()
            except ValueError as e:
                raise InvalidFileFormatError(self.input_file) from e  # column contains non-numeric values

            if len(sizes) == 0:
                raise EmptyMeasurementsError(self.input_file)
            
            return sizes
        
        except InvalidFileFormatError as e:
            logging.error(e.message)
            raise
            
        except EmptyMeasurementsError as e:
            logging.warning(e.message + " Skipping file.")
            return None
        
        except KeyError as e:
            er :MissingColumnError = MissingColumnError(self.particle_column_name, self.input_file)
            logging.error(er.message)
            raise er from e
        
        except (FileNotFoundError, PermissionError) as e:
            raise  # propagate raw so DirectoryCsvFileLoader can track them as invalid files
        
        except Exception as e:  # last-resort catch to ensure the error is logged
            logging.error(f"An unexpected error occurred while loading data from '{self.input_file}': {e}")
            raise


class ExcelFileLoader(FileLoader):
    """Loads particle sizes from a single XLSX file."""

    def __init__(self, input_file: Path, particle_column_index: int) -> None:
        self.input_file : Path = input_file
        self.particle_column_index : int = particle_column_index


    def _load_excel_to_dataframe(self) -> pd.DataFrame:
        """Reads an .xlsx file and returns a DataFrame."""
        try:
            # pd.read_excel uses openpyxl engine by default for .xlsx files
            # The header=None argument ensures that the first row is treated as data, not column names.
            df :pd.DataFrame = pd.read_excel(self.input_file, header=None)
            return df

        except FileNotFoundError:
            logging.error(f"Path to '{self.input_file}' not found (file does not exist).")
            raise

        except PermissionError:
            # common when the file is already open in Excel
            logging.error(f"You do not have permission to read the '{self.input_file}'. Check file locks or OS permissions.")
            raise

        except (zipfile.BadZipFile, ET.ParseError, InvalidFileException) as e:
            raise InvalidFileFormatError(self.input_file) from e  # not a valid .xlsx file

        except OSError as e:
            logging.error(f"System-level I/O error while reading an XLSX file occurred: {e}")
            raise

        except Exception as e:
            logging.error(f"Unexpected error reading XLSX content: {e}")
            raise


    def load_data(self) -> np.ndarray | None:
        try:
            df :pd.DataFrame = self._load_excel_to_dataframe()
            data :pd.Series = df.iloc[:, self.particle_column_index].dropna()
            try:
                sizes : np.ndarray = data.astype(str).str.replace(',', '.').astype(np.float64).to_numpy()
            except ValueError as e:
                raise InvalidFileFormatError(self.input_file) from e  # column contains non-numeric values
            
            if len(sizes) == 0:
                raise EmptyMeasurementsError(self.input_file)

            return sizes
        
        except InvalidFileFormatError as e:
            logging.error(e.message)
            raise

        except EmptyMeasurementsError as e:
            logging.warning(e.message + " Skipping file.")
            return None

        except IndexError as e:
            er :MissingColumnError = MissingColumnError("\"last column\"", self.input_file)
            logging.error(er.message)
            raise er from e
        
        except (FileNotFoundError, PermissionError, OSError):
            raise

        except Exception as e:
            logging.error(f"An unexpected error occurred while loading data from '{self.input_file}': {e}")
            raise