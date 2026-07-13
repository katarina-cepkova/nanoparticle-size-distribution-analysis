import argparse
import sys
from dash import Dash
from pathlib import Path

from domain_errors import AppError
from data_loader import DirectoryLoader, ConsoleLoader, ParticleSizesData
from file_loader import derive_dataset_label

from configuration import initialize_application
from configuration import SEPARATOR, END_OF_INPUT, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX
from configuration import INPUT_DATA_PATH, OUTPUT_DATA_PATH
from configuration import BIN_WIDTH_IN_NM

from moments import compute_moments, MomentsResult
from fitting import fit_lognormal, fit_normal, fit_lorentzian, FitResult
from ks_test import KSTestResult, compute_ks_test
from histogram import HistogramResult, compute_histogram, find_max_value

from output_printing import print_measurement_summary, print_moments_summary, print_fit_and_ks_table
from printer import Printer, FilePrinter, ConsolePrinter, CompositePrinter
from app import build_app



def parse_args() -> argparse.Namespace:
    """Parses and returns CLI arguments."""
    dataset_label : str | None = derive_dataset_label(INPUT_DATA_PATH)
    summary_suffix : str = "stat_summary.txt"
    summary_filename :str = f"{dataset_label}-{summary_suffix}" if dataset_label else summary_suffix
    summary_file_path :Path = OUTPUT_DATA_PATH / summary_filename

    parser :argparse.ArgumentParser = argparse.ArgumentParser(description="Nanoparticle size distribution analysis tool")
    parser.add_argument(
        "--source",
        choices=["console", "file"],
        default="file",
        help="Where to load particle size data from (default: file)"
    )
    parser.add_argument(
        "--output",
        nargs="+",
        choices=["console", "file"],
        default=["console", "file"],
        help="Where to write the report: 'console', 'file', or both (default: both).",
    )
    parser.add_argument(
        "--output-file",
        default=summary_file_path,
        help="Path to the statistic report file, used only when 'file' is included in --output."
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
    
    printers :list[Printer] = []
    if "console" in args.output:
        printers.append(ConsolePrinter())
    if "file" in args.output:
        printers.append(FilePrinter(args.output_file))

    printer :Printer = CompositePrinter(printers)

    try:
        # data and initial measures
        data: ParticleSizesData = data_loader.load_data()
        max_value :float = find_max_value(data.sizes)
        total_nanoparticles :int = len(data.sizes)
        print_measurement_summary(printer, data, total_nanoparticles)

        # moments
        moments: MomentsResult = compute_moments(data.sizes)
        print_moments_summary(printer, moments)

        # fitting
        normal_fit: FitResult = fit_normal(data.sizes)
        lognormal_fit: FitResult = fit_lognormal(data.sizes)
        lorentzian_fit: FitResult = fit_lorentzian(data.sizes)
        fits : list[FitResult] = [normal_fit, lognormal_fit, lorentzian_fit]
        # ks test
        ks_results :list[KSTestResult] = [compute_ks_test(data.sizes, fit) for fit in fits]
        print_fit_and_ks_table(printer, fits, ks_results)

        # app with histogram
        fit_results_by_distribution: dict[str, FitResult] = {fit.distribution: fit for fit in fits}
        histogram :HistogramResult = compute_histogram(data.sizes, BIN_WIDTH_IN_NM, max_value, total_nanoparticles)
        app :Dash = Dash(__name__)
        build_app(app, printer, data.sizes, histogram, fit_results_by_distribution)
        app.run()

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)
    finally:
        if isinstance(printer, FilePrinter):
            printer.close()


if __name__ == "__main__":
    main()