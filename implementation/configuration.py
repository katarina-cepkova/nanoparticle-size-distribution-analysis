from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from logging import Logger, StreamHandler, FileHandler
import flask.cli
import kaleido


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# loading environment variables regardless of the current working directory
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

SEPARATOR :str = os.getenv('SEPARATOR', '---')
END_OF_INPUT :str = os.getenv('END_OF_INPUT', 'END')

CSV_PARTICLE_COLUMN_NAME :str = os.getenv('CSV_COLUMN_NAME', 'Length')
XLSX_PARTICLE_COLUMN_INDEX :int = int(os.getenv('XLSX_COLUMN_INDEX', -1))  # default to -1 if not set

INPUT_DATA_PATH :Path = PROJECT_ROOT / os.getenv('INPUT_DATA_PATH', 'data/input_data')
OUTPUT_DATA_PATH :Path = PROJECT_ROOT / os.getenv('OUTPUT_DATA_PATH', 'data/output_data')
OUTPUT_GRAPH_PATH :Path = PROJECT_ROOT / os.getenv('OUTPUT_GRAPH_PATH', 'data/output_data/graphs')
OUTPUT_GRAPH_NAME_PREFIX :str = os.getenv('OUTPUT_GRAPH_NAME_PREFIX', 'histogram')
PNG_EXPORT_WIDTH_IN_PIXELS :int = int(os.getenv('PNG_EXPORT_WIDTH_IN_PIXELS', 1600))
PNG_EXPORT_HEIGHT_IN_PIXELS :int = int(os.getenv('PNG_EXPORT_HEIGHT_IN_PIXELS', 900))
PNG_EXPORT_SCALE :int = int(os.getenv('PNG_EXPORT_SCALE', 2))

LOG_DIR :Path = PROJECT_ROOT / os.getenv('LOG_DIR', 'logs')

DECIMAL_PLACES :int = int(os.getenv('DECIMAL_PLACES', 6))
PERCENTAGE_DECIMAL_PLACES :int = int(os.getenv('PERCENTAGE_DECIMAL_PLACES', 2))
ALPHA :float = float(os.getenv('ALPHA', 0.05))  # significance level for statistical tests
BIN_WIDTH_IN_NM : float = float(os.getenv('BIN_WIDTH', 0.25))


def _setup_directories() -> None:
    """Creates input, output, and log directories if they do not already exist."""
    # create input and output directories if they don't exist
    INPUT_DATA_PATH.mkdir(parents=True, exist_ok=True)
    OUTPUT_DATA_PATH.mkdir(parents=True, exist_ok=True)
    OUTPUT_GRAPH_PATH.mkdir(parents=True, exist_ok=True)

    # create a directory for logs if it doesn't exist
    LOG_DIR.mkdir(exist_ok=True)


def _setup_logging() -> None:
    """
    Sets up logging for the application. Logs will be written to both console and a log file.
    """
    # logger = input point
    # handler = output point
    logger :Logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # handler for console output - user-friendly messages
    console_handler :StreamHandler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # handler for file output - detailed logs
    file_handler :FileHandler = logging.FileHandler(LOG_DIR / 'app.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)   
    logger.addHandler(file_handler)

    # suppressing loggers
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    flask.cli.show_server_banner = lambda *args: None
    logging.getLogger("choreographer").setLevel(logging.WARNING)
    logging.getLogger("kaleido").setLevel(logging.WARNING)


def _ensure_chrome_available() -> None:
    """Downloads headless Chrome for kaleido if not already present."""
    try:
        kaleido.get_chrome_sync()
    except Exception as er:
        logging.error(f"Failed to ensure Chrome for kaleido: {er}")
        raise


def initialize_application() -> None:
    """
    Initializes the application by setting up directories and logging.
    """
    _setup_directories()
    _setup_logging()
    _ensure_chrome_available()