import argparse
import sys
from dash import Dash

from domain_errors import AppError
from data_loader import DirectoryLoader, ConsoleLoader, ParticleSizesData

from configuration import initialize_application
from configuration import SEPARATOR, END_OF_INPUT, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX
from configuration import INPUT_DATA_PATH, OUTPUT_DATA_PATH
from configuration import DECIMAL_PLACES, ALPHA, BIN_WIDTH_IN_NM

from moments import compute_moments, MomentsResult
from fitting import fit_lognormal, fit_normal, fit_lorentzian, FitResult
from ks_test import KSTestResult, compute_ks_test
from histogram import HistogramResult, compute_histogram, find_max_value

from output_printing import print_measurement_summary, print_moments_summary, print_fit_and_ks_table, print_histogram_summary
from printer import Printer, FilePrinter, ConsolePrinter

from histogram_visual import build_visual_histogram
from app import build_app

def parse_args() -> argparse.Namespace:
    """Parses and returns CLI arguments."""
    parser :argparse.ArgumentParser = argparse.ArgumentParser(description="Nanoparticle size distribution analysis tool")
    parser.add_argument(
        "--source",
        choices=["console", "file"],
        default="file",
        help="Where to load particle size data from (default: file)"
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Write the report to this .txt file instead of printing to the console. "
             "If omitted, the report is printed to the console."
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: initialises the app, selects a data loader, and prints statistical results."""
    initialize_application()
    args :argparse.Namespace = parse_args()

    if args.source == "console":
        data_loader :ConsoleLoader | DirectoryLoader = ConsoleLoader(SEPARATOR, END_OF_INPUT)
    else:  # args.source == "file"
        data_loader = DirectoryLoader(INPUT_DATA_PATH, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX)
    
    if args.output:
        printer: Printer = FilePrinter(OUTPUT_DATA_PATH / args.output)
    else:
        printer = ConsolePrinter()

    try:
        data: ParticleSizesData = data_loader.load_data()
        max_value :float = find_max_value(data.sizes)
        total_nanoparticles :int = len(data.sizes)

        print_measurement_summary(printer, data, total_nanoparticles)

        moments: MomentsResult = compute_moments(data.sizes)
        print_moments_summary(printer, moments)

        normal_fit: FitResult = fit_normal(data.sizes)
        lognormal_fit: FitResult = fit_lognormal(data.sizes)
        lorentzian_fit: FitResult = fit_lorentzian(data.sizes)
        fits : list[FitResult] = [normal_fit, lognormal_fit, lorentzian_fit]

        ks_results :list[KSTestResult] = [compute_ks_test(data.sizes, fit) for fit in fits]
        print_fit_and_ks_table(printer, fits, ks_results)

        histogram :HistogramResult = compute_histogram(data.sizes, BIN_WIDTH_IN_NM, max_value, total_nanoparticles)

        app :Dash = Dash(__name__)
        build_app(app, data.sizes, histogram)
        app.run()

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)
    finally:
        if isinstance(printer, FilePrinter):
            printer.close()


if __name__ == "__main__":
    main()