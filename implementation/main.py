import argparse
import sys
from dash import Dash
from pathlib import Path

from domain_errors import AppError
from data_loader import DataLoader, ParticleSizesData, ConsoleLoader, DirectoryLoader
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
from csv_output import write_histogram_to_csv, write_statistics_csv


def parse_args() -> argparse.Namespace:
    """Parses and returns CLI arguments."""
    dataset_label : str | None = derive_dataset_label(INPUT_DATA_PATH)
    summary_prefix : str = "stat_summary"
    summary_filename :str = f"{summary_prefix}_{dataset_label}" if dataset_label else summary_prefix
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
        "--output-txt-file",
        type=Path,
        default=OUTPUT_DATA_PATH / f"{summary_file_path}.txt",
        help="Path to the statistic report file, used only when 'file' is included in --output."
    )
    parser.add_argument(
        "--output-csv-file",
        type=Path,
        default=OUTPUT_DATA_PATH / f"{summary_file_path}.csv",
        help="Path to the statistic report file in csv format, used only when 'file' is included in --output."
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=["txt", "csv"],
        default=["txt"],
        help="File fomrat(s) for the report, used only when 'file' is included in --output (default: txt)."
    )
    return parser.parse_args()


def build_data_loader(args :argparse.Namespace) -> DataLoader:
    """Builds the data loader (console or directory) selected by the --source argument."""
    data_loader :DataLoader
    if args.source == "console":
        data_loader = ConsoleLoader(SEPARATOR, END_OF_INPUT)
    else:  # args.source == "file"
        data_loader = DirectoryLoader(INPUT_DATA_PATH, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX)
    return data_loader


def build_printer_for_console_app(args :argparse.Namespace) -> Printer:
    """Builds the composite printer for the initial statistics report, combining console 
    and/or file printers per the --output argument."""
    printers :list[Printer] = []
    if "console" in args.output:
        printers.append(ConsolePrinter())
    if "file" in args.output:
        printers.append(FilePrinter(args.output_txt_file))

    printer :Printer = CompositePrinter(printers)
    return printer


def build_printer_for_dash_app(args :argparse.Namespace) -> Printer:
    """Initializes a printer for the dash application. 
    File printer is left out as every histogram summary will be printed in a respective file."""
    app_printers :list[Printer] = []
    if "console" in args.output:
        app_printers.append(ConsolePrinter())
    app_printer :Printer = CompositePrinter(app_printers)

    return app_printer


def run_statistics(data :ParticleSizesData, printer :Printer, args: argparse.Namespace) -> tuple[float, int, dict[str, FitResult]]:
    """Prints the measurement summary, moments, and distribution fits with KS test results.

    Returns the max value, particle count, and fit results keyed by distribution
    name, which the caller needs to build the histogram and the dash app.
    """
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
    fit_results_by_distribution: dict[str, FitResult] = {fit.distribution: fit for fit in fits}

    # ks test
    ks_results :list[KSTestResult] = [compute_ks_test(data.sizes, fit) for fit in fits]
    print_fit_and_ks_table(printer, fits, ks_results)

    # print statistic results in csv if selected
    if "file" in args.output and "csv" in args.format:
        write_statistics_csv(args.output_csv_file, moments, fits, ks_results)
        
    return max_value, total_nanoparticles, fit_results_by_distribution


def main() -> None:
    """Entry point: initialises the app, selects a data loader, runs the statistics report,
    then launches the dash app with the histogram.

    Only data loading and statistics/app execution are wrapped in the try block below,
    since those are the only steps that can raise an AppError; building loaders and
    printers is pure configuration and can't fail that way.
    """
    initialize_application()
    args :argparse.Namespace = parse_args()
    data_loader : DataLoader = build_data_loader(args)
    printer :Printer = build_printer_for_console_app(args)
    app_printer :Printer = build_printer_for_dash_app(args)

    try:
        # data and initial measures
        data: ParticleSizesData = data_loader.load_data()
        max_value, total_nanoparticles, fit_results_by_distribution = run_statistics(data, printer, args)
        histogram :HistogramResult = compute_histogram(data.sizes, BIN_WIDTH_IN_NM, max_value, total_nanoparticles)

        app :Dash = Dash(__name__)
        build_app(app, app_printer, data.sizes, histogram, fit_results_by_distribution, "file" in args.output, args.format)
        app.run()

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)
    finally:
        printer.close()
        app_printer.close()


if __name__ == "__main__":
    main()