import argparse
import sys


from domain_errors import AppError
from data_loader import DirectoryLoader, ConsoleLoader, ParticleSizesData
from configuration import initialize_application
from configuration import SEPARATOR, END_OF_INPUT, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX, INPUT_DATA_PATH, OUTPUT_DATA_PATH, DECIMAL_PLACES
from moments import compute_moments, MomentsResult
from fitting import fit_lognormal, fit_normal, fit_lorentzian, FitResult



def parse_args() -> argparse.Namespace:
    """Parses and returns CLI arguments."""
    parser = argparse.ArgumentParser(description="Nanoparticle size distribution analysis tool")
    parser.add_argument(
        "--source",
        choices=["console", "file"],
        default="file",
        help="Where to load particle size data from (default: file)"
    )
    return parser.parse_args()



def print_section_header(title: str, length: int = 60) -> None:
    """Prints a section header with a title and separator lines."""
    
    title_length = len(title)
    if title_length > length:
        length = title_length + 4  # Adjust length to accommodate the title with padding
    left_padding = (length - title_length) // 2
    right_padding = length - title_length - left_padding
    print()
    print()
    print(' ' * left_padding + title + ' ' * right_padding)
    print('=' * length)
    print()
    

def print_measurement_summary(data: ParticleSizesData) -> None:
    """
    Prints a formatted table of per-source particle counts with a total row.
    """
    print_section_header("MEASUREMENT SUMMARY")

    sorted_counts :list[tuple[str, int]] = sorted(data.counts.items())
    max_filename_length = max(len(name) for name in data.counts)
    max_filename_length = max(max_filename_length+5, 30)
    # print header
    print(f"{'File/image':<{max_filename_length}}|{'Count':>10}")
    print('-'*(max_filename_length + 11))

    for name, count in sorted_counts:
        print(f"{name:<{max_filename_length}}|{count:>10,}")
    
    # print the total count
    print('-'*(max_filename_length + 11))
    print(f"{'TOTAL':<{max_filename_length}}|{sum(data.counts.values()):>10,}")
    print('-'*(max_filename_length + 11))


def print_moments_summary(moments: MomentsResult) -> None:
    """
    Prints a formatted summary of the computed statistical moments.
    """
    print_section_header("STATISTICAL MOMENTS")

    rows = [
        ("Mean (μ)", moments.mean),
        ("Variance (σ²)", moments.variance),
        ("Standard Deviation (σ)", moments.std),
        ("Skewness", moments.skewness),
        ("Coefficient of Variation (CV)", moments.cv),
        ("Median", moments.median),
        ("Polydispersity Index (PDI)", moments.PDI),
    ]

    label_width = max(len(label) for label, _ in rows)
    value_width = 10

    print(f"{'Metric':<{label_width}} | {'Value':>{value_width}}")
    print(f"{'-' * (label_width + value_width + 5)}")
    for label, value in rows:
        print(f"{label:<{label_width}} | {value:>{value_width}.{DECIMAL_PLACES}f}")
    print(f"{'-' * (label_width + value_width + 5)}")


def print_row(label: str, values: list[float | None], col_width : int, label_width: int) -> None:
    cells = []
    for val in values:
        if val is not None:
            cells.append(f"{val:>{col_width}.{DECIMAL_PLACES}f}")
        else:
            cells.append(f"{'':>{col_width}}")

    print(f"{label:<{label_width}} | " + " | ".join(cells))


def print_fits_comparison_table(fits: list[FitResult]) -> None:
    """
    Prints all three fitted distributions (normal, lognormal, cauchy) side by
    side in one table. Row labels are hardcoded since the set of distributions
    and their parameter names (mu/sigma vs x0/gamma) is fixed and won't change.
    A cell is left blank where a parameter doesn't apply to that distribution.
    """
    # (row label, key used to look up the value in fit.params) for distribution-specific rows
    param_keys = ["mu", "sigma", "x0", "gamma"]
 
    col_names :list[str] = [fit.distribution.capitalize() for fit in fits]
    label_width :int = max(len(key) for key in param_keys) 
    label_width :int = max(label_width, len("Log-Likelihood"))

    col_width = 12
    for name in col_names:
        col_width = max(col_width, len(name))
 
    # print header
    distribution_names :list[str] = []
    for name in col_names:
        distribution_names.append(f"{name:>{col_width}}")

    header = f"{'Metric':<{label_width}} | " + " | ".join(distribution_names)
    print(header)
    print('-' * len(header))
 
    # print distribution-specific parameters (mu/sigma for normal/lognormal, x0/gamma for cauchy)
    for key in param_keys:
        print_row(
            key.capitalize(),   [fit.params.get(key) for fit in fits],  col_width, label_width
        )
 
    # print distribution-independent parameters (log-likelihood, mode, fwhm
    print_row("Log-Likelihood", [fit.log_likelihood for fit in fits],   col_width, label_width)
    print_row("Mode",           [fit.mode for fit in fits],             col_width, label_width)
    print_row("FWHM",           [fit.fwhm for fit in fits],             col_width, label_width)
 
    print('-' * len(header))


def print_fit_summary(fit_result: FitResult) -> None:
    """
    Prints a formatted summary of the fitted distribution parameters.
    """
    rows = []
    for param, value in fit_result.params.items():
        rows.append((param.capitalize(), value))

    rows.append(("Log-Likelihood", fit_result.log_likelihood))
    rows.append(("Mode", fit_result.mode))
    rows.append(("FWHM", fit_result.fwhm))

    label_width = max(len(label) for label, _ in rows)
    value_width = 12

    print()
    print(f"{fit_result.distribution.capitalize()} Distribution Parameters:")
    print()
    print(f"{'Metric':<{label_width}} | {'Value':>{value_width}}")
    print(f"{'-' * (label_width + value_width + 5)}")
    for label, value in rows:
        print(f"{label:<{label_width}} | {value:>{value_width}.{DECIMAL_PLACES}f}")
    print(f"{'-' * (label_width + value_width + 5)}")
    print()


def print_complete_fit_summary(data: ParticleSizesData) -> None:
    """Fits all three distributions (normal, lognormal, cauchy) to the data and prints a comparison table of their parameters."""
    print_section_header("DISTRIBUTION FITTING")

    normal_fit: FitResult = fit_normal(data.sizes)
    lognormal_fit: FitResult = fit_lognormal(data.sizes)
    lorentzian_fit: FitResult = fit_lorentzian(data.sizes)
    fits : list[FitResult] = [normal_fit, lognormal_fit, lorentzian_fit]
    print_fits_comparison_table(fits)

    fit_with_max_likelihood :FitResult = max(fits, key=lambda fit: fit.log_likelihood)

    print_section_header(f"MAXIMUM LOG-LIKELIHOOD FIT = {fit_with_max_likelihood.distribution.upper()}")
    print_fit_summary(fit_with_max_likelihood)


def main():
    """Entry point: initialises the app, selects a data loader, and prints statistical results."""
    initialize_application()
    args = parse_args()

    if args.source == "console":
        data_loader = ConsoleLoader(SEPARATOR, END_OF_INPUT)
    else:  # args.source == "file"
        data_loader = DirectoryLoader(INPUT_DATA_PATH, CSV_PARTICLE_COLUMN_NAME, XLSX_PARTICLE_COLUMN_INDEX)
        
    try:
        data: ParticleSizesData = data_loader.load_data()
        print_measurement_summary(data)

        moments: MomentsResult = compute_moments(data.sizes)
        print_moments_summary(moments)

        print_complete_fit_summary(data)
        

    except AppError as e:
        print(f"Error: {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()