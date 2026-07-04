from dataclasses import dataclass
import numpy as np
from scipy import stats
import logging

from domain_errors import InvalidInputError


@dataclass
class MomentsResult:
    mean: float       # μ (mu) - arithmetic mean of the data
    variance: float   # σ² - variance, measure of spread around the mean
    std: float        # σ (sigma) - standard deviation, sqrt(variance)
    skewness: float   # skewness - measure of distribution asymmetry (0 = symmetric)
    cv: float         # coefficient of variation - relative variability (std/mean)
    median: float     # median - middle value of sorted data (robust to outliers)
    PDI: float        # polydispersity index - measure of size distribution width/uniformity
    D32: float        # Sauter mean diameter - sum(d^3) / sum(d^2), surface-area-weighted mean size


def compute_moments(data: np.ndarray) -> MomentsResult:
    mean : float = float(np.mean(data))                     # μ

    if (mean == 0):  # only if we have positive and negative values - particles cannot have negative size = invalid input
        er :InvalidInputError = InvalidInputError("Mean of the data is zero, cannot compute coefficient of variation or PDI.")
        logging.error(er.message)
        raise er

    # ddof=1: gives an unbiased estimate of variance (divide MLE by n-1 instead of n)
    variance: float = float(np.var(data, ddof=1))           # σ²
    std: float = float(np.std(data, ddof=1))                # σ

    # bias=False: same correction as ddof=1, applied to skewness estimation
    # positive = right-skewed, negative = left-skewed
    skewness : float = float(stats.skew(data, bias=False))
             
    cv: float = std / mean
    median : float = float(np.median(data))

    # PDI = (σ/μ)² = cv² - expresses how "polydisperse" (wide/non-uniform) the
    # size distribution is vs. "monodisperse" (narrow, similar particle sizes)
    PDI: float = variance / mean**2

    # D32 (Sauter mean diameter) = sum(d^3) / sum(d^2) - weights larger particles
    # more heavily than the arithmetic mean; common in particle-size analysis
    # since it reflects surface-area-to-volume ratio, not just count
    D32 : float = float(np.sum(data**3) / np.sum(data**2))

    return MomentsResult(mean, variance, std, skewness, cv, median, PDI, D32)