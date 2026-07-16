import csv
from pathlib import Path
from histogram import HistogramResult
from moments import MomentsResult
from fitting import FitResult
from ks_test import KSTestResult


def write_histogram_to_csv(histogram: HistogramResult, path: Path) -> None:
    """Writes one row per bin: edges, count, and percentage."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bin_left", "bin_right", "count", "percentage"])

        for i in range(histogram.bin_count):
            writer.writerow([
                histogram.bin_edges[i],
                histogram.bin_edges[i + 1],
                histogram.bin_counts[i],
                histogram.bin_percentages[i],
            ])


def write_statistics_csv(
        path: Path,
        moments: MomentsResult,
        fits: list[FitResult],
        ks_results: list[KSTestResult]
    ) -> None:
    """Writes one row: descriptive moments, plus per-distribution fit/KS values 
    with a distribution-name prefix."""
    header :list[str] = []
    values :list[object] = []

    def add(name: str, value: object) -> None:
        header.append(name)
        values.append(value)

    add("mean", moments.mean)
    add("median", moments.median)
    add("variance", moments.variance)
    add("std", moments.std)
    add("skewness", moments.skewness)
    add("cv", moments.cv)
    add("PDI", moments.PDI)
    add("D32", moments.D32)

    for fit, ks in zip(fits, ks_results):
        prefix :str = fit.distribution
        add(f"{prefix}_loc", fit.loc)
        add(f"{prefix}_scale", fit.scale)
        for param_name, param_value in fit.params.items():
            add(f"{prefix}_{param_name}", param_value)
        add(f"{prefix}_theoretical_mode", fit.theoretical_mode)
        add(f"{prefix}_theoretical_median", fit.theoretical_median)
        add(f"{prefix}_theoretical_mean", fit.theoretical_mean)
        add(f"{prefix}_theoretical_std", fit.theoretical_std)
        add(f"{prefix}_theoretical_cv", fit.theoretical_cv)
        add(f"{prefix}_theoretical_pdi", fit.theoretical_pdi)
        add(f"{prefix}_fwhm", fit.fwhm)
        add(f"{prefix}_rel_fwhm", fit.rel_fwhm)
        add(f"{prefix}_log_likelihood", fit.log_likelihood)
        add(f"{prefix}_ks_statistic", ks.statistic)
        add(f"{prefix}_ks_pvalue", ks.p_value)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(values)