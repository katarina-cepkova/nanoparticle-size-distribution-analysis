from data_loader import DirectoryLoader, ConsoleLoader, ParticleSizesData
from configuration import DECIMAL_PLACES, ALPHA
from moments import compute_moments, MomentsResult
from fitting import fit_lognormal, fit_normal, fit_lorentzian, FitResult
from ks_test import KSTestResult, compute_ks_test
from printer import Printer


# one labelled table row: a metric name plus its value for each fit/distribution
Row = tuple[str, list[float | str | None]]
# every distribution-specific parameter name that can appear in a fit's `params` dict
PARAM_KEYS = ["mu", "sigma", "x0", "gamma"]


def print_section_header(printer: Printer, title: str, length: int = 60) -> None:
    """Prints a section header with a title and separator lines."""

    title_length = len(title)
    if title_length > length:
        length = title_length + 4  # Adjust length to accommodate the title with padding
    # split the padding left/right so the title sits centered within `length`
    left_padding = (length - title_length) // 2
    right_padding = length - title_length - left_padding
    printer.print()
    printer.print()
    printer.print(' ' * left_padding + title + ' ' * right_padding)
    printer.print('=' * length)
    printer.print()


def print_measurement_summary(printer: Printer, data: ParticleSizesData) -> None:
    """
    Prints a formatted table of per-source particle counts with a total row.
    """
    print_section_header(printer, "MEASUREMENT SUMMARY")

    sorted_counts :list[tuple[str, int]] = sorted(data.counts.items())
    max_filename_length = max(len(name) for name in data.counts)
    max_filename_length = max(max_filename_length+5, 30)  # +5 padding, floor of 30 for short names
    # print header
    printer.print(f"{'File/image':<{max_filename_length}}|{'Count':>10}")
    printer.print('-'*(max_filename_length + 11))

    for name, count in sorted_counts:
        printer.print(f"{name:<{max_filename_length}}|{count:>10,}")

    # print the total count
    printer.print('-'*(max_filename_length + 11))
    printer.print(f"{'TOTAL':<{max_filename_length}}|{sum(data.counts.values()):>10,}")
    printer.print('-'*(max_filename_length + 11))


def print_moments_summary(printer: Printer, moments: MomentsResult) -> None:
    """
    Prints a formatted summary of the computed statistical moments.
    """
    print_section_header(printer, "STATISTICAL MOMENTS")

    rows = [
        ("Mean (μ)", moments.mean),
        ("Variance (σ²)", moments.variance),
        ("Standard Deviation (σ)", moments.std),
        ("Skewness", moments.skewness),
        ("Coefficient of Variation (CV)", moments.cv),
        ("Median", moments.median),
        ("Polydispersity Index (PDI)", moments.PDI),
        ("Sauter mean diameter (D32)", moments.D32)
    ]

    label_width = max(len(label) for label, _ in rows)
    value_width = 10

    printer.print(f"{'Metric':<{label_width}} | {'Value':>{value_width}}")
    printer.print(f"{'-' * (label_width + value_width + 3)}")
    for label, value in rows:
        printer.print(f"{label:<{label_width}} | {value:>{value_width}.{DECIMAL_PLACES}f}")
    printer.print(f"{'-' * (label_width + value_width + 3)}")


def print_row(printer: Printer, label: str, values: list[float | str | None], col_width : int, label_width: int) -> None:
    """
    Prints one table row: a left-aligned label followed by one right-aligned
    cell per value. Each value is formatted according to its type:
    - float -> fixed-point number with DECIMAL_PLACES decimals
    - str   -> printed as-is (e.g. a verdict like "BEST" or "REJECTED")
    - None  -> printed as a blank cell (e.g. a parameter that doesn't apply
      to a given distribution, like "x0" for a normal fit)
    """
    cells = []
    for val in values:
        if isinstance(val, float):
            cells.append(f"{val:>{col_width}.{DECIMAL_PLACES}f}")
        elif isinstance(val, str):
            cells.append(f"{val:>{col_width}}")
        else:  # None
            cells.append(f"{'':>{col_width}}")

    printer.print(f"{label:<{label_width}} | " + " | ".join(cells))


def get_table_widths(fits: list[FitResult], rows: list[Row]) -> tuple[int, int]:
    """
    Computes the shared label/column widths so header, fit rows, and KS rows all line up.
    col_width is derived from the actual data: the widest formatted number (using
    DECIMAL_PLACES from .env) across all rows, so a large log-likelihood like
    -123456.789012 still fits without hardcoding an assumed width.
    """
    col_names = [fit.distribution.capitalize() for fit in fits]
    label_width = max(len(label) for label, _ in rows)
    label_width = max(label_width, len("Metric"))

    # collect only the numeric values to find the largest magnitude, then measure
    # the formatted width from that single value — no need to format every value
    signed_widest :float = 0.0
    for _, values in rows:
        for v in values:
            if isinstance(v, float) and abs(v) > abs(signed_widest):
                signed_widest = v
            elif isinstance(v, float) and abs(v) == abs(signed_widest):
                # if two values have the same magnitude, prefer the negative one for
                # signed_widest so we reserve space for the "-" sign in the table
                signed_widest = min(signed_widest, v)

    max_value_width = len(f"{signed_widest:.{DECIMAL_PLACES}f}")
    
    # separately track the widest text cell (e.g. verdicts like "REJECTED"),
    # since text values aren't formatted with DECIMAL_PLACES like numbers are
    max_text_width = 0
    for label, values in rows:
        for v in values:
            if isinstance(v, str):
                max_text_width = max(max_text_width, len(v))
        if isinstance(label, str):
            max_text_width = max(max_text_width, len(label))

    col_width = max(max_value_width, max_text_width, 12)

    # also make sure the column is wide enough for the distribution name itself
    # (e.g. "Lognormal" is longer than most single formatted values)
    for name in col_names:
        col_width = max(col_width, len(name))

    return label_width, col_width


def print_table_header(printer: Printer, fits: list[FitResult], label_width: int, col_width: int) -> int:
    """
    Prints the header row for a table of distribution fits.
    Returns the total width of the header line for use in printing a separator line.
    """
    col_names :list[str] = [fit.distribution.capitalize() for fit in fits]
    distribution_names :list[str] = [f"{name:>{col_width}}" for name in col_names]
    header = f"{'Metric':<{label_width}} | " + " | ".join(distribution_names)
    printer.print(header)
    header_width = len(header)
    printer.print('-' * header_width)
    return header_width


def print_grouped_distribution_table(printer: Printer, fits: list[FitResult], row_groups: list[list[Row]]) -> None:
    """
    Prints a table with one column per fit, made up of several groups of rows.
    A '-' divider is printed after every group — so a new group is exactly how
    you "ask" for a divider at that point, no separate marker is needed.
    Widths are computed once across all groups so everything lines up under a
    single shared header.
    """
    all_rows = [row for group in row_groups for row in group]
    label_width, col_width = get_table_widths(fits, all_rows)
    header_width = print_table_header(printer, fits, label_width, col_width)

    for group in row_groups:
        for label, values in group:
            print_row(printer, label, values, col_width, label_width)
        printer.print('-' * header_width)  # divider after every group, including the last


def build_fit_rows(fits: list[FitResult]) -> list[Row]:
    """
    Builds the comparison rows for the fit-parameters part of the table:
    distribution-specific params (mu/sigma from PARAM_KEYS, e.g. "mu"/"sigma"
    for normal & lognormal, "x0"/"gamma" for cauchy), log-likelihood plus a
    "BEST" verdict marking the highest one, mode, and FWHM. A cell is left
    blank where a parameter doesn't apply to a given distribution (via
    fit.params.get(key), which returns None if the key is missing).
    """

    # one row per parameter name; params.get(key) is None for distributions that don't have it
    rows :list[Row] = [
        (key.capitalize(), [fit.params.get(key) for fit in fits]) for key in PARAM_KEYS
    ]
    rows.append(("Log-Likelihood", [fit.log_likelihood for fit in fits]))

    # mark whichever fit has the highest log-likelihood as the best-fitting distribution
    best_log_likelihood :float = max(fit.log_likelihood for fit in fits)
    ll_verdict :list[float | str | None]  = ["BEST" if fit.log_likelihood == best_log_likelihood else "" for fit in fits]

    rows.append(("LL Verdict",      ll_verdict))
    rows.append(("Theoretical mode",    [fit.theoretical_mode for fit in fits]))
    rows.append(("Theoretical median",  [fit.theoretical_median for fit in fits]))
    rows.append(("FWHM",                [fit.fwhm for fit in fits]))
    rows.append(("Relative FWHM",       [fit.rel_fwhm for fit in fits]))
    rows.append(("Location",            [fit.loc for fit in fits]))
    rows.append(("Scale",               [fit.scale for fit in fits]))

    return rows


def build_ks_rows(ks_results: list[KSTestResult]) -> list[Row]:
    """
    Builds the comparison rows for the KS-test part of the table: the KS
    statistic, the p-value, and a "REJECTED" verdict for any distribution
    whose p-value falls below the ALPHA significance level (blank otherwise).
    """
    
    rows :list[Row] = [
        ("KS Statistic", [result.statistic for result in ks_results]),
        ("P-value",   [result.p_value for result in ks_results]),
        # null hypothesis (data follows this distribution) is rejected below the ALPHA threshold
        ("KS Verdict", ["REJECTED" if result.p_value < ALPHA else "" for result in ks_results])
    ]

    return rows


def print_fit_and_ks_table(printer: Printer, fits: list[FitResult], ks_results: list[KSTestResult]) -> None:
    """
    Prints one combined section: a section header followed by a single table
    that shows fit parameters (mu/sigma/x0/gamma, log-likelihood + winner,
    mode, FWHM) and KS test results (statistic, p-value, verdict) side by
    side per distribution, with a divider line between the two blocks.
    """
    print_section_header(printer, "DISTRIBUTION FITTING and KS TEST RESULTS")

    fit_rows :list[Row] = build_fit_rows(fits)
    ks_rows :list[Row] = build_ks_rows(ks_results)

    print_grouped_distribution_table(printer, fits, [fit_rows, ks_rows])