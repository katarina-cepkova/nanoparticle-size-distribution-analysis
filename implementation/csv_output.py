import csv
from pathlib import Path
from histogram import HistogramResult


def write_histogram_to_csv(histogram :HistogramResult, path :Path) -> None:
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


