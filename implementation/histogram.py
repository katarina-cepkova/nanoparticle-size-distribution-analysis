from dataclasses import dataclass
import numpy as np
import logging
from domain_errors import InvalidInputError


@dataclass
class HistogramResult:
    bin_edges: np.ndarray    # bin boundaries; length is bin_count + 1
    bin_counts: np.ndarray   # particle count per bin; length is bin_count
    bin_count: int           # number of bins the data was split into
    empirical_mode: float    # midpoint of the most populated bin (the histogram-based "most common" size, not a fitted-curve estimate)


def bin_edges_from_width(data: np.ndarray, bin_width: float) -> np.ndarray:
    """Build evenly spaced bin edges of the given width spanning the data's range."""

    # np.arange's stop bound is exclusive, so add one extra bin_width to
    # make sure the max data point lands inside the last bin, not on its edge.
    min :float = 0.0
    max :float = float(np.max(data))
    return np.arange(min, max+bin_width, bin_width)


def compute_histogram(data: np.ndarray, bin_width: float) -> HistogramResult:
    """Bin the data into a histogram and derive the empirical mode from it."""

    if bin_width <= 0.0:
        er :InvalidInputError = InvalidInputError(f"Bin width must be positive, got '{bin_width}'.")
        logging.error(er.message)
        raise er

    bin_edges :np.ndarray = bin_edges_from_width(data, bin_width)
    bin_counts :np.ndarray

    # bins=<int> would ask numpy to compute that many equal-width bins;
    # bins=<ndarray> uses those exact edges, so we get back the edges we passed in.
    bin_counts, bin_edges = np.histogram(data, bins=bin_edges)
    bin_count = len(bin_edges) - 1
    # Index of the tallest bin, i.e. the most populated size range.
    max_bin_index :int = int(np.argmax(bin_counts))
    # empirical = calculated from the data
    empirical_mode :float = float((bin_edges[max_bin_index] + bin_edges[max_bin_index + 1]) / 2)  # no index out of range, num of bin_edges is bin_count + 1

    return HistogramResult(
        bin_edges=bin_edges,
        bin_counts=bin_counts,
        bin_count=bin_count,
        empirical_mode=empirical_mode
    )
