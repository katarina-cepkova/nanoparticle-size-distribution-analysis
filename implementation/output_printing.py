import datetime
from datetime import datetime

from data_loader import ParticleSizesData
from configuration import DECIMAL_PLACES, PERCENTAGE_DECIMAL_PLACES, ALPHA
from moments import MomentsResult
from fitting import FitResult
from ks_test import KSTestResult
from printer import Printer
from histogram import HistogramResult

# one labelled table row: a row label plus one value per column
Row = tuple[str, list[float | int | str | None]]
# every distribution-specific parameter name that can appear in a fit's `params` dict
PARAM_KEYS :list[str] = ["mu", "sigma", "x0", "gamma"]


def print_section_header(printer: Printer, title: str, length: int = 60) -> None:
    """Prints a section header with a title and separator lines."""

    title_length :int = len(title)
    if title_length > length:
        length = title_length + 4  # Adjust length to accommodate the title with padding
    # split the padding left/right so the title sits centered within `length`
    left_padding :int = (length - title_length) // 2
    right_padding :int = length - title_length - left_padding
    printer.print()
    printer.print()
    printer.print(' ' * left_padding + title + ' ' * right_padding)
    printer.print('=' * length)
    printer.print()


def print_measurement_summary(printer: Printer, data: ParticleSizesData, total_nanoparticles: int) -> None:
    """
    Prints a formatted table of per-source particle counts with a total row.
    """
    sorted_counts :list[tuple[str, int]] = sorted(data.counts.items())
    row_groups :list[list[Row]] = [
        [(name, [count]) for name, count in sorted_counts],
        [("TOTAL", [total_nanoparticles])]
    ]
    all_rows :list[Row] = [row for group in row_groups for row in group]

    col_names :list[str] = ["Count"]
    label_width, col_width = get_table_widths(col_names, all_rows, label_header="File/image")
    header :str = build_table_header_string(col_names, label_width, col_width, label_header="File/image")
    header_width :int = len(header)

    print_section_header(printer, "MEASUREMENT SUMMARY", header_width)
    print_table_header(printer, header)

    for group in row_groups:
        for label, values in group:
            print_row(printer, label, values, col_width, label_width)
        printer.print('-' * header_width)  # divider after every group, including the last


def print_moments_summary(printer: Printer, moments: MomentsResult) -> None:
    """
    Prints a formatted summary of the computed statistical moments.
    """

    row_groups :list[list[Row]] = [
        # central tendency — different ways of describing the "typical" particle size
        [
            ("Mean (μ)", [moments.mean]),
            ("Median", [moments.median]),
            ("Sauter mean diameter (D32)", [moments.D32]),
        ],
        # spread — absolute measures of variability (same units as the data / squared units)
        [
            ("Variance (σ²)", [moments.variance]),
            ("Standard Deviation (σ)", [moments.std]),
        ],
        # spread — relative/dimensionless measures of variability (PDI = CV²)
        [
            ("Coefficient of Variation (CV)", [moments.cv]),
            ("Polydispersity Index (PDI)", [moments.PDI]),
        ],
        # shape — asymmetry of the distribution
        [
            ("Skewness", [moments.skewness]),
        ],
    ]
    all_rows :list[Row] = [row for group in row_groups for row in group]

    col_names :list[str] = ["Value"]
    label_width, col_width = get_table_widths(col_names, all_rows)
    header :str = build_table_header_string(col_names, label_width, col_width)
    header_width :int = len(header)

    print_section_header(printer, "STATISTICAL MOMENTS", header_width)
    print_table_header(printer, header)

    for i, group in enumerate(row_groups):
        for label, values in group:
            print_row(printer, label, values, col_width, label_width)
        if i < len(row_groups) - 1:
            print_row(printer, "", [None] * (len(col_names)), col_width, label_width)  # blank separator between groups of related metrics
    printer.print('-' * header_width)


def print_row(printer: Printer, label: str, values: list[float | int | str | None], col_width: int, label_width: int) -> None:
    """
    Prints one table row: a left-aligned label followed by one right-aligned
    cell per value. Each value is formatted according to its type:
    - float -> fixed-point number with DECIMAL_PLACES decimals
    - int   -> whole number with thousands separators (e.g. a particle count)
    - str   -> printed as-is (e.g. a verdict like "BEST" or "REJECTED")
    - None  -> printed as a blank cell (e.g. a parameter that doesn't apply
      to a given distribution, like "x0" for a normal fit)
    """
    cells :list[str] = []
    for val in values:
        if isinstance(val, float):
            cells.append(f"{val:>{col_width}.{DECIMAL_PLACES}f}")
        elif isinstance(val, int):
            cells.append(f"{val:>{col_width},}")
        elif isinstance(val, str):
            cells.append(f"{val:>{col_width}}")
        else:  # None
            cells.append(f"{'':>{col_width}}")

    printer.print(f"{label:<{label_width}} | " + " | ".join(cells))


def get_table_widths(col_names: list[str], rows: list[Row], label_header: str = "Metric", min_col_width: int = 12) -> tuple[int, int]:
    """
    Computes the shared label/column widths so header and data rows all line up.
    col_width is derived from the actual data: the widest formatted number (using
    DECIMAL_PLACES from .env) across all rows, so a large log-likelihood like
    -123456.789012 still fits without hardcoding an assumed width.
    """
    label_width :int = max(len(label) for label, _ in rows)
    label_width = max(label_width, len(label_header))

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

    max_value_width :int = len(f"{signed_widest:.{DECIMAL_PLACES}f}")

    # separately track the widest int cell (e.g. a particle count), since
    # ints are formatted with thousands separators rather than DECIMAL_PLACES
    max_int_width :int = 0
    for _, values in rows:
        for v in values:
            if isinstance(v, int):
                max_int_width = max(max_int_width, len(f"{v:,}"))

    # separately track the widest text cell (e.g. verdicts like "REJECTED"),
    # since text values aren't formatted with DECIMAL_PLACES like numbers are
    max_text_width :int = 0
    for label, values in rows:
        for v in values:
            if isinstance(v, str):
                max_text_width = max(max_text_width, len(v))

    col_width :int = max(max_value_width, max_int_width, max_text_width, min_col_width)

    # also make sure the column is wide enough for the column name itself
    # (e.g. "Lognormal" is longer than most single formatted values)
    for name in col_names:
        col_width = max(col_width, len(name))

    return label_width, col_width


def build_table_header_string(col_names: list[str], label_width: int, col_width: int, label_header: str = "Metric") -> str:
    """
    Builds the 'Metric | Normal | Lognormal | Lorentzian' header line as a
    plain string, without printing it. Used both by print_table_header (to
    print it) and by callers that need to know the table's width in advance —
    e.g. to size the '=' bar in print_section_header to match the table below it.
    """
    formatted_names :list[str] = [f"{name:>{col_width}}" for name in col_names]
    return f"{label_header:<{label_width}} | " + " | ".join(formatted_names)


def print_table_header(printer: Printer, header: str) -> int:
    """
    Prints the header row for a table of distribution fits.
    Returns the total width of the header line for use in printing a separator line.
    """
    printer.print(header)
    header_width :int = len(header)
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
    col_names :list[str] = [fit.distribution.capitalize() for fit in fits]
    all_rows :list[Row] = [row for group in row_groups for row in group]
    label_width, col_width = get_table_widths(col_names, all_rows)

    header :str = build_table_header_string(col_names, label_width, col_width)
    header_width :int = len(header)
    print_section_header(printer, "DISTRIBUTION FITTING and KS TEST RESULTS", header_width)
    print_table_header(printer, header)

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

    rows.append(("Location",            [fit.loc for fit in fits]))
    rows.append(("Scale",               [fit.scale for fit in fits]))
    rows.append(("", [None] * len(fits)))
    rows.append(("Theoretical mean",    [fit.theoretical_mean for fit in fits]))
    rows.append(("Theoretical median",  [fit.theoretical_median for fit in fits]))
    rows.append(("Theoretical mode",    [fit.theoretical_mode for fit in fits]))
    rows.append(("Theoretical Std",     [fit.theoretical_std for fit in fits]))
    rows.append(("Theoretical CV",     [fit.theoretical_cv for fit in fits]))
    rows.append(("Theoretical PDI",     [fit.theoretical_pdi for fit in fits]))
    rows.append(("FWHM",                [fit.fwhm for fit in fits]))
    rows.append(("Relative FWHM",       [fit.rel_fwhm for fit in fits]))
    rows.append(("", [None] * len(fits)))
    rows.append(("Log-Likelihood",      [fit.log_likelihood for fit in fits]))

    # mark whichever fit has the highest log-likelihood as the best-fitting distribution
    best_log_likelihood :float = max(fit.log_likelihood for fit in fits)
    ll_verdict :list[float | str | None]  = ["BEST" if fit.log_likelihood == best_log_likelihood else "" for fit in fits]
    rows.append(("LL Verdict",          ll_verdict))

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
    fit_rows :list[Row] = build_fit_rows(fits)
    ks_rows :list[Row] = build_ks_rows(ks_results)

    print_grouped_distribution_table(printer, fits, [fit_rows, ks_rows])


def compute_num_of_digits(bin_count: int) -> int:
    """Digit width needed to print bin numbers 1..bin_count right-aligned."""
    digits :int = 0
    remaining :int = bin_count
    while remaining > 0:
        remaining //= 10
        digits += 1
    
    return digits


def format_date_pretty(header_width: int) -> str:
    """Formats date and time info and aligns to the right according to the header_width"""
    timestamp :str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix :str = "Date and time:"
    aligned_date :str = f"{prefix}{timestamp:>{max(header_width - len(prefix), 0)}}"
    return aligned_date


def print_histogram_summary(printer: Printer, histogram: HistogramResult, code: str) -> None:
    """
    Prints bin count, empirical mode, and the full bin-by-bin breakdown
    (size range -> particle count) in one simple Metric | Value table.
    """
    bin_rows :list[Row] = []
    digits :int = compute_num_of_digits(histogram.bin_count)

    for i in range(histogram.bin_count):
        left :float = float(histogram.bin_edges[i])
        right :float = float(histogram.bin_edges[i+1])
        closing_bracket :str
        if i == histogram.bin_count - 1:
            closing_bracket = "]"
        else:
            closing_bracket = ")"
        interval :str = f"{i+1:>{digits}}  [{left:.{DECIMAL_PLACES}f}; {right:.{DECIMAL_PLACES}f}{closing_bracket}"
        percentage :str = f"{histogram.bin_percentages[i]:.{PERCENTAGE_DECIMAL_PLACES}f}"
        bin_rows.append((interval, [int(histogram.bin_counts[i]), percentage]))

    row_groups :list[list[Row]] = [
        [
            ("Nanoparticle count", [histogram.nanoparticle_count, f"{100:.{PERCENTAGE_DECIMAL_PLACES}f}"]),
            ("Bin width (nm)", [histogram.bin_width, None])
        ],
        bin_rows,
    ]
    all_rows :list[Row] = [row for group in row_groups for row in group]

    col_names :list[str] = ["Count", "Percentage (%)"]
    label_width, col_width = get_table_widths(col_names, all_rows)
    header :str = build_table_header_string(col_names, label_width, col_width)
    header_width :int = len(header)

    print_section_header(printer, f"HISTOGRAM SUMMARY – {code}", header_width)
    printer.print(format_date_pretty(header_width))
    print_table_header(printer, header)

    for i, group in enumerate(row_groups):
        for label, values in group:
            print_row(printer, label, values, col_width, label_width)
        if i < len(row_groups) - 1:
            printer.print()  # blank separator between groups of related rows
    printer.print('-' * header_width)
